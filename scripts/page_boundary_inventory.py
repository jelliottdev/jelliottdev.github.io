"""Inventory transcription edges, without inferring manuscript word joins."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/page-boundaries.json'


def report():
    index_bytes = (ROOT / 'data/index.json').read_bytes()
    alphabet = {entry['rune'] for entry in json.loads(index_bytes)['alphabet']}
    pages = []
    for number in range(56):
        page_id = f'lp2-{number:02d}'
        blob = (ROOT / f'data/pages/{page_id}.json').read_bytes()
        page = json.loads(blob)
        raw = page['raw']
        working = raw.replace('/', '').strip()
        pages.append(dict(page=page_id, record_sha256=hashlib.sha256(blob).hexdigest(),
                          raw_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                          original_start=raw[:40], original_end=raw[-40:],
                          working_start=working[:40], working_end=working[-40:]))
    boundaries = []
    for left, right in zip(pages, pages[1:]):
        end, start = left['working_end'][-1:], right['working_start'][:1]
        boundaries.append(dict(left=left['page'], right=right['page'],
                               left_edge=end, right_edge=start,
                               rune_to_rune=end in alphabet and start in alphabet,
                               visual_review='not-performed', word_join='undetermined'))
    count = sum(row['rune_to_rune'] for row in boundaries)
    assert len(boundaries) == 55
    return dict(scope='55 adjacent boundaries from LP2-00 through LP2-55; excludes transitions to LP2-56 and LP2-57.',
                method='Use raw text only. Remove every slash (archival row marker), strip outer whitespace, then test the last and first Unicode characters against the stored rune alphabet. No other punctuation is removed.',
                limitation='Rune-to-rune edges are candidates for review, not confirmed split words. Section changes, punctuation omitted in a transcription and non-runic material require image inspection. This is not a catalogue of disputed readings.',
                alphabet_source_sha256=hashlib.sha256(index_bytes).hexdigest(),
                counts=dict(boundaries=55, rune_to_rune=count, other=55-count),
                pages=pages, boundaries=boundaries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: 55 boundary classifications, exact edge slices and source hashes')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
