"""Check LP2-57 sums against archived 761.MP3 metadata; no audio decoding.

Default: inspect the exact 206-byte ID3 excerpt bundled with this script.
--mp3 PATH: verify the complete archive file's SHA-256 and extract its tag.
--write saves the ledger; --check compares it with the saved result.
"""
import argparse
import hashlib
import json
from math import prod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = '83008217439110c3b824898af73b99cb2cf0657dda88cb363c3aa34a4ec0a460'
TAG = ROOT / 'exports/761-id3.bin'
OUTPUT = ROOT / 'exports/parable-mp3-link.json'


def tag_bytes(data):
    assert data[:6] == b'ID3\x03\x00\x00', 'Expected unflagged ID3v2.3'
    assert all(x < 128 for x in data[6:10])
    size = sum(x << (7 * (3-i)) for i, x in enumerate(data[6:10]))
    assert len(data) >= 10 + size
    return data[:10+size]


def report(data):
    data = tag_bytes(data)
    frames, offset = [], 10
    while offset < len(data) and data[offset] != 0:
        name = data[offset:offset+4].decode('ascii')
        size = int.from_bytes(data[offset+4:offset+8], 'big')
        assert data[offset+8:offset+10] == b'\0\0'
        payload = data[offset+10:offset+10+size]
        assert len(payload) == size and payload[0] == 0, 'Expected Latin-1 text frame'
        frames.append(dict(frame=name, offset=offset, size=size, text=payload[1:].decode('latin1')))
        offset += 10+size
    texts = {f['frame']:f['text'] for f in frames}
    assert texts['TIT2'] == 'The Instar Emergence'
    source = ROOT / 'text/lp2-57.txt'
    alphabet_path = ROOT / 'data/index.json'
    alphabet = json.loads(alphabet_path.read_bytes())['alphabet']
    by_rune = {x['rune']:x['prime'] for x in alphabet}
    raw = source.read_text(encoding='utf-8')
    segments = [[by_rune[c] for c in part if c in by_rune] for part in raw.split('.')]
    segments = [s for s in segments if s]
    sums = list(map(sum, segments))
    assert sums == [449, 1259, 1031, 1229]
    tag_number = int(texts['TXXX'].split('\0')[0].removeprefix('Parable ').replace(',',''))
    assert prod(sums[1:]) == tag_number
    # Explicit title encoding, not an unspecified English-to-rune converter.
    words = [['TH','E'], ['I','N','S','T','A','R'], ['E','M','E','R','G','E','N','C','E']]
    values = {x['latin']:x['prime'] for x in alphabet}
    word_sums = [sum(values[x] for x in word) for word in words]
    assert word_sums == [72,280,409] and sum(word_sums) == 761
    return dict(mp3_sha256=SHA, id3_sha256=hashlib.sha256(data).hexdigest(), id3_bytes=len(data),
                archive_url='https://raw.githubusercontent.com/scream314/cicada3301/10733feb487bb8beb9966d534727ee5897aa54fc/assets/2013/cicados/AUDIO/761.MP3',
                source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,alphabet_path]},
                frames=frames, segment_values=segments, heading_sum=sums[0], body_sums=sums[1:],
                body_product=prod(sums[1:]), tag_number=tag_number,
                title_encoding=words, title_word_sums=word_sums, title_sum=sum(word_sums),
                limits=['Archived file identity is not independent signature authentication.',
                        'Title uses TH as one rune and C for the soft c in Emergence.',
                        'Multiplication does not establish sentence order or a cipher for unsolved pages.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mp3', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = args.mp3.read_bytes() if args.mp3 else TAG.read_bytes()
    if args.mp3:
        assert hashlib.sha256(data).hexdigest() == SHA, 'Different MP3 archive bytes'
        assert tag_bytes(data) == TAG.read_bytes(), 'Excerpt differs from original tag'
    result = report(data)
    if args.write:
        OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    elif args.check:
        assert json.loads(OUTPUT.read_bytes()) == result, 'Saved ledger differs'
        print('PASS: three body sums, metadata product, title encoding and saved ledger match.')
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
