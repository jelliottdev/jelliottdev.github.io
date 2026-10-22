"""Rebuild the archived 2013 Twitter bytes, Gematria JPEG and whitespace text."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'exports/sources/cicada-2013-twitter'
REPORT = ROOT / 'exports/cicada-2013-twitter.json'
FIGURE = ROOT / 'exports/figures/cicada-2013-twitter-chain.svg'
SIGNATURE_REPORT = ROOT / 'exports/cicada-2013-twitter-signature.json'
PUBLIC_KEY = ROOT / 'exports/steganography/cicada-public-key.asc'
FINGERPRINT = '6D854CD7933322A601C3286D181F01E57A35090F'


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_sources():
    manifest_raw = (HERE / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    assert manifest['revision'] == 'ade9a02889ef8acbc8cde8edbfd0a785c369f4c3'
    assets = {}
    for item in manifest['files']:
        name = item['file']
        assert name in {'full.txt', 'twitter.bin', '761.mp3', 'gematria.jpg', 'gematria.jpg.asc'}
        raw = (HERE / name).read_bytes()
        git_blob = hashlib.sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest()
        assert len(raw) == item['size'], name
        assert sha256(raw) == item['sha256'], name
        assert git_blob == item['git_blob_sha1'], name
        assets[name] = raw
    assert len(assets) == 5
    return assets, sha256(manifest_raw)


def rebuild_tweets(raw):
    rows = []
    for line_number, line in enumerate(raw.decode('ascii').splitlines(), 1):
        match = re.fullmatch(r'([0-9a-f]+): ([0-9a-f]+)', line)
        if not match or len(match[2]) % 2:
            raise ValueError(f'Invalid tweet line {line_number}')
        rows.append((int(match[1], 16), bytes.fromhex(match[2])))
    rows.sort(key=lambda row: row[0])
    if not rows or rows[0][0] != 0:
        raise ValueError('The offset list does not start at zero')
    chunks, next_offset = [], 0
    for offset, data in rows:
        if offset != next_offset:
            raise ValueError(f'Gap or overlap at offset {offset}; expected {next_offset}')
        chunks.append(data)
        next_offset += len(data)
    return b''.join(chunks), rows


def jpeg_size(raw):
    if not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):
        raise ValueError('Missing JPEG start or end marker')
    position = 2
    while position + 4 <= len(raw):
        if raw[position] != 0xff:
            raise ValueError('Invalid JPEG segment marker')
        marker = raw[position+1]
        if marker == 0xda:
            break
        segment_length = int.from_bytes(raw[position+2:position+4], 'big')
        if segment_length < 2 or position + 2 + segment_length > len(raw):
            raise ValueError('Invalid JPEG segment length')
        if marker in (0xc0, 0xc1, 0xc2):
            height = int.from_bytes(raw[position+5:position+7], 'big')
            width = int.from_bytes(raw[position+7:position+9], 'big')
            return [width, height]
        position += 2 + segment_length
    raise ValueError('JPEG size marker not found')


def decode_whitespace(raw):
    rows = [line for line in raw.splitlines() if line and set(line) <= {9, 32}]
    if not rows:
        raise ValueError('No space/tab-only rows')
    decoded = []
    for row in rows:
        if len(row) % 8:
            raise ValueError('Space/tab row is not byte-aligned')
        bits = ''.join('1' if character == 9 else '0' for character in row)
        decoded.append(bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8)).decode('ascii'))
    return decoded, [len(row) for row in rows]


def report():
    assets, manifest_hash = verify_sources()
    tweets, rows = rebuild_tweets(assets['full.txt'])
    assert tweets == assets['twitter.bin']
    audio = assets['761.mp3']
    if len(audio) < len(tweets):
        raise ValueError('The audio operand is shorter than the tweet bytes')
    jpeg = bytes(left ^ right for left, right in zip(tweets, audio))
    assert jpeg == assets['gematria.jpg']
    message, lengths = decode_whitespace(assets['gematria.jpg.asc'])
    return {
        'schema': 'liberpedia-2013-twitter-replay-v1',
        'source_revision': 'ade9a02889ef8acbc8cde8edbfd0a785c369f4c3',
        'manifest_sha256': manifest_hash,
        'inputs_sha256': {name: sha256(raw) for name, raw in assets.items()},
        'tweet_dump': {'rows': len(rows), 'lowest_offset': rows[0][0],
                       'highest_offset': rows[-1][0], 'last_row_bytes': len(rows[-1][1]),
                       'contiguous_bytes': len(tweets), 'gaps': 0, 'overlaps': 0,
                       'reconstructed_matches_archived_twitter_bin': True},
        'xor': {'operation': 'twitter.bin[i] XOR 761.mp3[i], for i=0..64166',
                'audio_bytes': len(audio), 'bytes_used': len(tweets),
                'output_bytes': len(jpeg), 'output_sha256': sha256(jpeg),
                'matches_archived_gematria_jpeg': True, 'jpeg_dimensions': jpeg_size(jpeg)},
        'outguess_payload': {'archived_bytes': len(assets['gematria.jpg.asc']),
                             'sha256': sha256(assets['gematria.jpg.asc']),
                             'fresh_retest_receipt': 'exports/cicada-2013-twitter-outguess.json',
                             'signature_receipt': 'exports/cicada-2013-twitter-signature.json'},
        'whitespace': {'rule': 'Each nonempty space/tab-only payload row is read left to right; space=0, tab=1; consecutive groups of eight bits form ASCII bytes.',
                       'rows': len(lengths), 'bits_per_row': lengths, 'decoded_lines': message},
        'limits': 'This replays preserved archived bytes and the hidden whitespace text. Signature verification is separately recorded; the replay does not recreate the live 2013 Twitter feed or contact the historical onion service.'
    }


def figure(data):
    boxes = [
        ('Offset-tagged posts', f'{data["tweet_dump"]["rows"]} rows · pinned full.txt', 'Sort by offset; require contiguous, nonoverlapping bytes'),
        ('twitter.bin', f'{data["tweet_dump"]["contiguous_bytes"]:,} bytes', 'Matches the archived intermediate exactly'),
        ('XOR with 761.mp3', f'first {data["xor"]["bytes_used"]:,} audio bytes', 'One audio byte per reconstructed tweet byte'),
        ('gematria.jpg', f'{data["xor"]["jpeg_dimensions"][0]} × {data["xor"]["jpeg_dimensions"][1]} pixels', 'Matches the archived JPEG exactly'),
        ('OutGuess payload', f'{data["outguess_payload"]["archived_bytes"]:,} bytes', 'Fresh local extraction matched archived signed bytes'),
        ('Space/tab rows', '4 rows · 552 bits', 'ASCII text is a separate layer within the payload')]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="840" viewBox="0 0 720 840" role="img" aria-labelledby="title desc">',
             '<title id="title">2013 Twitter to Gematria Primus: verified byte path</title>',
             '<desc id="desc">Six steps connect 988 offset-tagged lines to reconstructed Twitter bytes, XOR with archived audio, the Gematria JPEG, OutGuess extraction and a four-line whitespace message.</desc>',
             '<rect width="720" height="840" fill="#fff"/>',
             '<text x="40" y="42" font-family="Georgia,serif" font-size="29" fill="#20242a">From Twitter bytes to Gematria Primus</text>']
    for i, (title, detail, note) in enumerate(boxes):
        y = 70 + i * 125
        parts.extend([f'<rect x="40" y="{y}" width="640" height="92" fill="#f5f7f8" stroke="#c8d0d6"/>',
                      f'<text x="58" y="{y+29}" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#203f56">{title}</text>',
                      f'<text x="58" y="{y+52}" font-family="Arial,sans-serif" font-size="15" fill="#20242a">{detail}</text>',
                      f'<text x="58" y="{y+75}" font-family="Arial,sans-serif" font-size="13" fill="#5c626b">{note}</text>'])
        if i < len(boxes) - 1:
            parts.append(f'<path d="M360 {y+95} v25 m-6 -7 6 7 6 -7" fill="none" stroke="#315d76" stroke-width="2"/>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def check_outguess(executable, assets):
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'extracted.asc'
        process = subprocess.run([str(executable), '-r', str(HERE / 'gematria.jpg'), str(target)],
                                 capture_output=True, text=True, timeout=60)
        if process.returncode != 0 or not target.is_file():
            raise RuntimeError(f'OutGuess extraction failed: {process.stdout} {process.stderr}')
        if target.read_bytes() != assets['gematria.jpg.asc']:
            raise ValueError('Fresh OutGuess output differs from archived signed bytes')
        print(f'PASS: fresh OutGuess output matches {len(assets["gematria.jpg.asc"])} archived bytes; executable SHA-256 {sha256(Path(executable).read_bytes())}')


def verify_signature(executable, signed_bytes):
    if not executable.is_file():
        raise ValueError('GPG executable not found')
    public_key = PUBLIC_KEY.read_bytes()
    if sha256(public_key) != '1e1992b73916c356ffda19c3c1cbdfb206e6318910b0f502aa1e6e49a1fa41c7':
        raise ValueError('Preserved public key hash changed')
    with tempfile.TemporaryDirectory(prefix='liberpedia-2013-twitter-gpg-') as directory:
        home = Path(directory) / 'keyring'
        home.mkdir()
        payload = Path(directory) / 'gematria.jpg.asc'
        payload.write_bytes(signed_bytes)
        prefix = [str(executable.resolve()), '--no-options', '--homedir', str(home), '--batch',
                  '--no-tty', '--no-auto-key-retrieve']
        imported = subprocess.run(prefix + ['--import', str(PUBLIC_KEY)], capture_output=True,
                                  text=True, errors='replace', timeout=30)
        if imported.returncode:
            raise RuntimeError('Could not import the preserved public key')
        checked = subprocess.run(prefix + ['--status-fd', '1', '--verify', str(payload)],
                                 capture_output=True, text=True, errors='replace', timeout=30)
    valid = checked.returncode == 0 and f'[GNUPG:] VALIDSIG {FINGERPRINT}' in checked.stdout
    if not valid:
        raise RuntimeError('The payload signature did not verify with the preserved key')
    return {
        'schema': 'liberpedia-2013-twitter-signature-v1',
        'payload_path': 'exports/sources/cicada-2013-twitter/gematria.jpg.asc',
        'payload_sha256': sha256(signed_bytes),
        'public_key_path': 'exports/steganography/cicada-public-key.asc',
        'public_key_sha256': sha256(public_key),
        'gpg_executable_sha256': sha256(executable.read_bytes()),
        'valid_signature': True,
        'fingerprint': FINGERPRINT,
        'key_trust': 'not independently certified',
        'scope': 'Verifies the archived payload, which the separate OutGuess receipt matched byte for byte. It does not establish who controlled the key or reconstruct the live feed.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate report and SVG')
    parser.add_argument('--check', action='store_true', help='Verify report and SVG byte for byte')
    parser.add_argument('--outguess', type=Path, help='Optionally rerun extraction with this executable')
    parser.add_argument('--gpg', type=Path, help='Optionally verify the archived signed payload in an isolated keyring')
    args = parser.parse_args()
    result = report()
    output = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    visual = figure(result).encode('utf-8')
    if args.write:
        REPORT.write_bytes(output)
        FIGURE.write_bytes(visual)
    elif args.check:
        assert REPORT.read_bytes() == output
        assert FIGURE.read_bytes() == visual
        print('PASS: pinned sources, 988 offset rows, XOR, JPEG and whitespace text reproduce')
    else:
        print(output.decode('utf-8'))
    if args.outguess:
        assets, _ = verify_sources()
        check_outguess(args.outguess, assets)
    if args.gpg:
        assets, _ = verify_sources()
        receipt = (json.dumps(verify_signature(args.gpg, assets['gematria.jpg.asc']), indent=2) + '\n').encode('utf-8')
        if args.write:
            SIGNATURE_REPORT.write_bytes(receipt)
        elif args.check:
            assert SIGNATURE_REPORT.read_bytes() == receipt
        print(f'PASS: payload signature verifies with {FINGERPRINT}')


if __name__ == '__main__':
    main()
