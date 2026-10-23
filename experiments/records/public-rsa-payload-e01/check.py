"""Independent RSA arithmetic, source-modulus witness and structural checks."""
import base64
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
PINS = {r['path']: r['sha256'] for r in PLAN['inputs']}


def pinned(path):
    relative = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINS[relative], relative
    return raw


def key_packets(armored):
    body = re.search(rb'-----BEGIN PGP PUBLIC KEY BLOCK-----(.*?)-----END PGP PUBLIC KEY BLOCK-----',
                     armored, re.S).group(1)
    lines = [s.strip() for s in body.splitlines() if s.strip() and not s.startswith(b'=') and b':' not in s]
    stream = base64.b64decode(b''.join(lines))
    pos = 0
    while pos < len(stream):
        flag = stream[pos]
        assert flag & 0x80
        pos += 1
        if flag & 0x40:
            tag = flag & 0x3f
            length_byte = stream[pos]
            pos += 1
            if length_byte < 192:
                length = length_byte
            elif length_byte < 224:
                length = ((length_byte - 192) << 8) + stream[pos] + 192
                pos += 1
            elif length_byte == 255:
                length = int.from_bytes(stream[pos:pos + 4], 'big')
                pos += 4
            else:
                raise ValueError('partial length unsupported by pinned key')
        else:
            tag = (flag >> 2) & 0x0f
            form = flag & 3
            if form == 0:
                length = stream[pos]
                pos += 1
            elif form == 1:
                length = int.from_bytes(stream[pos:pos + 2], 'big')
                pos += 2
            elif form == 2:
                length = int.from_bytes(stream[pos:pos + 4], 'big')
                pos += 4
            else:
                raise ValueError('indeterminate length unsupported by pinned key')
        packet = stream[pos:pos + length]
        assert len(packet) == length
        pos += length
        if tag in (6, 14) and packet[0] == 4 and packet[5] in (1, 2, 3):
            bits = int.from_bytes(packet[6:8], 'big')
            count = (bits + 7) // 8
            n = int.from_bytes(packet[8:8 + count], 'big')
            epos = 8 + count
            ebits = int.from_bytes(packet[epos:epos + 2], 'big')
            e = int.from_bytes(packet[epos + 2:epos + 2 + (ebits + 7) // 8], 'big')
            fp = hashlib.sha1(b'\x99' + len(packet).to_bytes(2, 'big') + packet).hexdigest().upper()
            yield fp, n, e


DIGEST_PREFIXES = tuple(bytes.fromhex(s) for s in (
    '3021300906052b0e03021a05000414', '3031300d060960864801650304020105000420',
    '3041300d060960864801650304020205000430', '3051300d060960864801650304020305000440',
    '3020300c06082a864886f70d020505000410', '302d300d060960864801650304020405001c'))


def v15_signature(block):
    if not block.startswith(b'\x00\x01'):
        return None
    pad = 2
    while pad < len(block) and block[pad] == 255:
        pad += 1
    if pad - 2 < 8 or pad >= len(block) or block[pad] != 0:
        return None
    tail = block[pad + 1:]
    return 'strict' if any(tail.startswith(prefix) for prefix in DIGEST_PREFIXES) else 'loose'


def v15_encryption(block):
    if not block.startswith(b'\x00\x02'):
        return None
    end = block.find(b'\x00', 2)
    return 'loose' if end >= 10 else None


def pss(block, bits):
    if not block or block[-1] != 0xbc:
        return None
    best = None
    for constructor in (hashlib.sha1, hashlib.sha256, hashlib.sha384, hashlib.sha512):
        hlen = constructor().digest_size
        if len(block) < hlen + 2:
            continue
        masked = block[:-hlen - 1]
        digest = block[-hlen - 1:-1]
        mask = b''
        for counter in range((len(masked) + hlen - 1) // hlen):
            mask += constructor(digest + counter.to_bytes(4, 'big')).digest()
        data = bytearray(a ^ b for a, b in zip(masked, mask))
        extra = len(block) * 8 - bits
        if extra:
            data[0] &= 255 >> extra
        prefix = 0
        while prefix < len(data) and data[prefix] == 0:
            prefix += 1
        if prefix < len(data) and data[prefix] == 1:
            if prefix >= 8:
                return 'strict'
            best = 'loose'
    return best


def main():
    source = HERE / 'source'
    work = source / 'liber-primus/analysis/round18/L5-payload'
    source_mod = json.loads(pinned(work / 'moduli.json'))
    armored = pinned(source / 'corpus/A-primary-artifacts/pgp/keys/cicada-3301-pubkey.keys.openpgp.org.asc')
    observed = {fp: (n, e) for fp, n, e in key_packets(armored)}
    assert len(source_mod['pgp_moduli']) == 2
    for row in source_mod['pgp_moduli']:
        assert observed[row['fingerprint']] == (int(row['n_hex'], 16), row['e'])
        assert int(row['n_hex'], 16).bit_length() == row['bits'] == 4096
    welcome = pinned(source / 'liber-primus/analysis/armada20/pgp_welcome.txt').decode('utf-8')
    number_text = welcome.split('n = ', 1)[1].split('\n\n', 1)[0]
    n2013 = int(''.join(re.findall(r'\d+', number_text)))
    assert n2013 == int(source_mod['other_moduli'][0]['n_hex'], 16)
    assert n2013.bit_length() == 432

    moduli = [(row['fingerprint'][-16:] + '/' + row['role'], int(row['n_hex'], 16), row['fingerprint'])
              for row in source_mod['pgp_moduli']]
    moduli += [(row['name'], int(row['n_hex'], 16), None) for row in source_mod['other_moduli']]
    payloads = {'canon_majority': pinned(source / 'liber-primus/analysis/pp49_51/canon_256.bin'),
                'canon_decimal_preferred': pinned(source / 'liber-primus/analysis/pp49_51/canon_256_decpref.bin'),
                'L5_resolved': pinned(work / 'payload_resolved.bin')}
    assert all(len(value) == 256 for value in payloads.values())
    rows = []
    skipped = []
    for name, n, fingerprint in moduli:
        size = (n.bit_length() + 7) // 8
        embits = n.bit_length() - 1
        for pname, payload in payloads.items():
            encodings = [('big_endian', payload), ('little_endian', payload[::-1])]
            if size > 256:
                padding = b'\x00' * (size - 256)
                encodings.extend([('big_endian_left_aligned', payload + padding),
                                  ('little_endian_left_aligned', payload[::-1] + padding)])
            for enc_name, data in encodings:
                value = int.from_bytes(data, 'big')
                if value >= n:
                    skipped.append((name, pname, enc_name))
                    continue
                for e in (65537, 3, 17):
                    transformed = pow(value, e, n)
                    block = transformed.to_bytes(size, 'big')
                    pss_block = (transformed.to_bytes((embits + 7) // 8, 'big')
                                 if transformed.bit_length() <= embits else block)
                    for matcher, fn, target in (
                        ('pkcs1_v15_signature', v15_signature, block),
                        ('pkcs1_v15_encryption', v15_encryption, block),
                        ('emsa_pss', lambda v: pss(v, embits), pss_block)):
                        rows.append({'modulus': name, 'fingerprint': fingerprint,
                                     'bits': n.bit_length(), 'payload': pname,
                                     'encoding': enc_name, 'e': e, 'matcher': matcher,
                                     'tier': fn(target), 'result_head': block[:8].hex()})
    archived = json.loads(pinned(HERE / 'source-expected.json'))
    assert rows == archived['rows'] and all(row['tier'] is None for row in rows)
    assert len(rows) == archived['tuples_evaluated'] == 162
    assert len(skipped) == len(archived['tuples_skipped']) == 12
    assert set(skipped) == {(x['modulus'], x['payload'], x['encoding']) for x in archived['tuples_skipped']}
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert result['strict_hit_count'] == result['loose_hit_count'] == 0
    assert result['source_rows_sha256'] == hashlib.sha256(json.dumps(rows, sort_keys=True,
                                                              separators=(',', ':')).encode()).hexdigest()
    assert result['plan_sha256'] == hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest()
    # Deterministic structural-positive controls independent of random RSA keys.
    valid = b'\x00\x01' + b'\xff' * 8 + b'\x00' + DIGEST_PREFIXES[1] + b'\x11' * 32
    assert v15_signature(valid) == 'strict'
    assert v15_encryption(b'\x00\x02' + b'\x11' * 8 + b'\x00hello') == 'loose'
    print('Independent check: PGP primary/subkey fingerprints, 2013 modulus, 162 RSA rows and structural controls')


if __name__ == '__main__':
    main()
