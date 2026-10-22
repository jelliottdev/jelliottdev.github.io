"""Independent checks for the pinned 2013 Twitter-to-Gematria byte chain."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'exports/sources/cicada-2013-twitter'


def main():
    report = json.loads((ROOT / 'exports/cicada-2013-twitter.json').read_bytes())
    lines = (SOURCE / 'full.txt').read_bytes().splitlines()
    parsed = sorted((int(line.split(b': ', 1)[0], 16), bytes.fromhex(line.split(b': ', 1)[1].decode('ascii')))
                    for line in lines)
    end = max(offset + len(chunk) for offset, chunk in parsed)
    rebuilt = bytearray(end)
    coverage = bytearray(end)
    for offset, chunk in parsed:
        for index, value in enumerate(chunk, offset):
            assert coverage[index] == 0, f'Overlap at {index}'
            coverage[index] = 1
            rebuilt[index] = value
    assert all(coverage), 'Gap in tweet offsets'
    assert len(parsed) == report['tweet_dump']['rows'] == 988
    assert len(rebuilt) == report['tweet_dump']['contiguous_bytes'] == 64167
    assert bytes(rebuilt) == (SOURCE / 'twitter.bin').read_bytes()
    audio = (SOURCE / '761.mp3').read_bytes()
    jpeg = (SOURCE / 'gematria.jpg').read_bytes()
    assert len(jpeg) == len(rebuilt)
    assert bytes(jpeg[index] ^ audio[index] for index in range(len(jpeg))) == bytes(rebuilt)
    assert hashlib.sha256(jpeg).hexdigest() == report['xor']['output_sha256']
    assert jpeg[:3] == b'\xff\xd8\xff' and jpeg[-2:] == b'\xff\xd9'
    payload = (SOURCE / 'gematria.jpg.asc').read_bytes()
    rows = [row for row in payload.splitlines() if row and all(c in (9, 32) for c in row)]
    decoded = []
    for row in rows:
        assert len(row) % 8 == 0
        decoded.append(''.join(chr(sum((1 << (7-bit)) for bit, c in enumerate(row[i:i+8]) if c == 9))
                               for i in range(0, len(row), 8)))
    assert decoded == report['whitespace']['decoded_lines']
    receipt = json.loads((ROOT / 'exports/cicada-2013-twitter-outguess.json').read_bytes())
    assert receipt['input_sha256'] == report['xor']['output_sha256']
    assert receipt['output_sha256'] == hashlib.sha256(payload).hexdigest()
    assert receipt['output_bytes'] == len(payload)
    print('PASS: independent offset assembly, reverse XOR, payload rows and extraction receipt')


if __name__ == '__main__':
    main()
