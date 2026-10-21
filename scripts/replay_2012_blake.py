"""Replay the second-chance code on the preserved, line-formatted Blake text."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'exports/sources/blake-2012'
REPORT = ROOT / 'exports/cicada-2012-blake.json'


def replay():
    manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        assert hashlib.sha256((SOURCE / entry['file']).read_bytes()).hexdigest() == entry['sha256'], entry['file']
    text = (SOURCE / 'formatted.txt').read_bytes().decode('utf-8')
    lines = text.splitlines()
    assert len(lines) == 18 and text.isascii()
    payload = (SOURCE / 'payload.bin').read_bytes().decode('utf-8')
    body = payload.split('-----BEGIN PGP SIGNATURE-----')[0]
    coordinates = re.findall(r'(?m)^(\d+):(\d+)$', body)
    rows = []
    for a, b in coordinates:
        line, position = int(a), int(b)
        unit = lines[line-1]
        assert 1 <= position <= len(unit)
        selected = unit[position-1]
        assert selected == next(c for i,c in enumerate(unit,1) if i==position)
        rows.append(dict(coordinate=f'{a}:{b}', line=line, position=position,
                         text=unit, before=unit[:position-1], selected=selected, after=unit[position:]))
    output = ''.join(r['selected'] for r in rows)
    assert len(rows) == 22 and output == 'cginiziglyaobyph.onion'
    return dict(source_manifest=manifest, method='One-based physical-text line and character; heading omitted. Retain spaces, punctuation, numbered-list labels and the printed hyphenated line break. Only newline separators are excluded from line strings.',
                source_lines=lines, lookups=rows, output=output,
                checks='All input hashes; 18 ASCII text lines; 22 in-bounds lookups; direct indexing agrees with iterative counting; historical expected output.',
                image_review='The archived 373 by 504 plate was visually compared for the 18-line layout and split princi-/ples. Fine punctuation is faint; no character-perfect facsimile certification is claimed.',
                limitations='Replays the preserved formatted text and an already extracted payload. Does not freshly verify PGP, redo OutGuess or contact the historical onion service. The plate image does not establish the precise original edition used by every solver.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = replay()
    if args.check:
        assert result == json.loads(REPORT.read_text(encoding='utf-8'))
        print('PASS: all 22 Blake coordinates, preserved input hashes and historical output')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
