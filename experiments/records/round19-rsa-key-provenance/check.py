"""Independent key-packet, modular-power, provenance, and row checks."""
import base64
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"
ROOT = HERE.parents[2]


def packets(raw):
    for match in re.finditer(rb"-----BEGIN PGP PUBLIC KEY BLOCK-----(.*?)-----END PGP PUBLIC KEY BLOCK-----", raw, re.S):
        lines = [line.strip() for line in match.group(1).splitlines()
                 if line.strip() and not line.strip().startswith(b"=") and b":" not in line]
        stream = base64.b64decode(b"".join(lines))
        p = 0
        while p < len(stream):
            flag = stream[p]
            assert flag & 128
            p += 1
            if flag & 64:
                tag = flag & 63
                b = stream[p]
                p += 1
                if b < 192:
                    length = b
                elif b < 224:
                    length = ((b - 192) << 8) + stream[p] + 192
                    p += 1
                elif b == 255:
                    length = int.from_bytes(stream[p:p + 4], "big")
                    p += 4
                else:
                    raise AssertionError("unsupported partial packet")
            else:
                tag = (flag >> 2) & 15
                form = flag & 3
                width = [1, 2, 4][form]
                length = int.from_bytes(stream[p:p + width], "big")
                p += width
            body = stream[p:p + length]
            assert len(body) == length
            p += length
            if tag not in (6, 14) or len(body) < 8 or body[0] != 4 or body[5] not in (1, 2, 3):
                continue
            nbits = int.from_bytes(body[6:8], "big")
            nend = 8 + (nbits + 7) // 8
            n = int.from_bytes(body[8:nend], "big")
            ebits = int.from_bytes(body[nend:nend + 2], "big")
            e = int.from_bytes(body[nend + 2:nend + 2 + (ebits + 7) // 8], "big")
            fp = hashlib.sha1(b"\x99" + len(body).to_bytes(2, "big") + body).hexdigest().upper()
            yield fp, n, e


def structural(block, nbits):
    # Independent Boolean checks for the exact source acceptance predicates.
    if block.startswith(b"\x00\x01"):
        p = 2
        while p < len(block) and block[p] == 255:
            p += 1
        if p >= 10 and p < len(block) and block[p] == 0:
            return True
    if block.startswith(b"\x00\x02"):
        p = block.find(b"\x00", 2)
        if p >= 10 and p < len(block) - 1:
            return True
    for hf in (hashlib.sha1, hashlib.sha256, hashlib.sha384, hashlib.sha512):
        hlen = hf().digest_size
        for candidate, bits in ((block, nbits),
                                ((int.from_bytes(block, "big") % (1 << (nbits - 1))).to_bytes(((nbits - 1) + 7) // 8, "big"), nbits - 1)):
            if len(candidate) < hlen + 2 or candidate[-1] != 0xbc:
                continue
            masked, h = candidate[:-hlen - 1], candidate[-hlen - 1:-1]
            mask = b"".join(hf(h + i.to_bytes(4, "big")).digest()
                            for i in range((len(masked) + hlen - 1) // hlen))[:len(masked)]
            db = bytearray(a ^ b for a, b in zip(masked, mask))
            spare = len(candidate) * 8 - bits
            if spare:
                db[0] &= 255 >> spare
            for salt in {0, 20, 28, 32, 48, 64, hlen}:
                zeros = len(candidate) - hlen - salt - 2
                if zeros >= 0 and bytes(db[:zeros]) == b"\x00" * zeros and db[zeros] == 1:
                    return True
    return False


def main():
    plan = json.loads((HERE / "plan.json").read_text())
    for pin in plan["inputs"]:
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    old = json.loads((SRC / "out_e01.json").read_text())
    current = json.loads((HERE / "results.json").read_text())
    mapping = json.loads((SRC / "witness-map.json").read_text())
    keys = {}
    for path in mapping.values():
        for fp, n, e in packets((SRC / path).read_bytes()):
            keys[fp] = (n, e)
    assert len(keys) == current["pgp_packets"] == 22
    original = json.loads((SRC / "moduli.json").read_text())
    cicada = {x["fingerprint"] for x in original["pgp_moduli"]}
    assert len(cicada) == 2 and cicada <= keys.keys()
    for item in original["pgp_moduli"]:
        assert keys[item["fingerprint"]] == (int(item["n_hex"], 16), item["e"])
    numbered = {}
    for item in old["moduli_tested"]:
        if item["fingerprint"]:
            numbered[item["name"]] = keys[item["fingerprint"]]
        else:
            other = next(x for x in original["other_moduli"] if x["name"] == item["name"])
            numbered[item["name"]] = (int(other["n_hex"], 16), other["e"])
    payloads = {name: (SRC / f"{name}.bin").read_bytes() for name in old["payload_variants"]}
    count = {"SKIP": 0, "NULL": 0, "HIT": 0}
    for row in old["rows"]:
        n, _ = numbered[row["modulus"]]
        data = payloads[row["payload"]]
        value = int.from_bytes(data, row["endian"])
        size = (n.bit_length() + 7) // 8
        if row["align"] == "left":
            value <<= 8 * (size - len(data))
        if value >= n:
            assert row["verdict"] == "SKIP"
        else:
            block = pow(value, row["e"], n).to_bytes(size, "big")
            assert block[:12].hex() == row["head_hex"]
            assert ("HIT" if structural(block, n.bit_length()) else "NULL") == row["verdict"]
        count[row["verdict"]] += 1
    assert count == {"SKIP": 144, "NULL": 594, "HIT": 0}
    assert current["cicada_pgp_packets"] == 2 and current["other_archived_pgp_packets"] == 20
    assert current["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    assert structural(b"\x00\x01" + b"\xff" * 8 + b"\x00" + b"\x30" * 32, 43 * 8)
    assert structural(b"\x00\x02" + b"\x01" * 8 + b"\x00X", 12 * 8)
    print("Independent check: 22 PGP fingerprints, 738 source rows, no structure, key provenance")


if __name__ == "__main__":
    main()
