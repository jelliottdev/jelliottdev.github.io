"""Replay archived Liber AL coordinates; no network access or third-party libraries."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'exports/sources/cicada-2013'
REPORT = ROOT / 'exports/cicada-2013-liber-al.json'


def replay():
    manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        assert hashlib.sha256((SOURCE / entry['file']).read_bytes()).hexdigest() == entry['sha256'], entry['file']
    chapters = {}
    for chapter in ('I', 'II', 'III'):
        text = (SOURCE / f'book-of-the-law-{chapter}.txt').read_bytes().decode('utf-8')
        headings = list(re.finditer(r'(?m)^(\d+)\. ', text))
        assert [int(h[1]) for h in headings] == list(range(1, len(headings)+1))
        verses = {}
        for i, heading in enumerate(headings):
            raw = text[heading.end():headings[i+1].start() if i+1 < len(headings) else len(text)]
            clean = raw.replace(' ', '').replace('\n', '')
            assert '\r' not in clean and '\t' not in clean
            verses[int(heading[1])] = dict(raw=raw, working=clean)
        # Compare anchored verse parsing with the archive's unanchored split rule.
        alternate = re.split(r'\d+\. ', text)[1:]
        assert [v['working'] for v in verses.values()] == [v.replace(' ', '').replace('\n', '') for v in alternate]
        chapters[chapter] = verses
    payload = (SOURCE / '232.jpg.asc').read_text(encoding='utf-8')
    body = payload.split('-----BEGIN PGP SIGNATURE-----')[0]
    tokens = re.findall(r'(?m)^(?:I{1,3}:\d+:\d+|[05])$', body)
    rows = []
    for token in tokens:
        if ':' not in token:
            rows.append(dict(token=token, kind='literal', selected=token))
            continue
        chapter, verse, position = token.split(':')
        unit = chapters[chapter][int(verse)]
        offset = int(position)-1
        assert 0 <= offset < len(unit['working'])
        selected = unit['working'][offset]
        by_iteration = next(c for i, c in enumerate(unit['working'], 1) if i == int(position))
        assert selected == by_iteration
        rows.append(dict(token=token, kind='lookup', chapter=chapter, verse=int(verse),
                         one_based_position=int(position), raw_verse=unit['raw'], working_verse=unit['working'],
                         selected=selected))
    raw_output = ''.join(r['selected'] for r in rows)
    assert len(rows) == 46 and sum(r['kind']=='literal' for r in rows) == 2
    assert raw_output == 'https:--www.dropbox.com-s-r7sgeb5dtmzj14s-3301'
    return dict(source_manifest=manifest, method='One-based chapter, numbered verse and character. Remove verse labels, ASCII spaces and LF newlines only; retain punctuation and case. Literal 5 and 0 bypass lookup.',
                verification='Source hashes checked; anchored and unanchored verse parsers agree; direct and iterative character selection agree; historical expected output checked after extraction.',
                limitations='Replays an archived working copy, not proof of the exact edition originally used. This script does not extract the JPEG payload or verify the PGP signature. No historical URL is contacted.',
                verse_counts={k:len(v) for k,v in chapters.items()}, lookups=rows,
                raw_output=raw_output, interpreted_output=raw_output.replace('-', '/'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = replay()
    if args.check:
        assert result == json.loads(REPORT.read_text(encoding='utf-8'))
        print('PASS: complete Liber AL lookup trace, literals, source hashes and raw/interpreted output')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
