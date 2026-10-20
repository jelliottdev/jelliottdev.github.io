"""Inventory published transcription layers; this does not perform visual review."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/transcription-coverage.json'


def report():
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    alphabet = {a['rune'] for a in index['alphabet']}
    records = []
    for page in index['pages']:
        path = ROOT / 'data/pages' / (page['id'] + '.json')
        blob = path.read_bytes()
        data = json.loads(blob)
        raw = data['raw']
        reviewed = data.get('reviewed_text')
        original_runes = ''.join(c for c in raw if c in alphabet)
        alternative_runes = None if reviewed is None else ''.join(c for c in reviewed if c in alphabet)
        kind = ('no-separate-reviewed-layer' if reviewed is None else
                'identical-text' if raw == reviewed else
                'non-rune-changes-only' if original_runes == alternative_runes else
                'rune-stream-changed')
        records.append(dict(page=data['id'], layer_status=kind,
                            archived_rune_count=len(original_runes),
                            reviewed_rune_count=None if reviewed is None else len(alternative_runes),
                            correction_notes=data.get('corrections', []),
                            page_record_sha256=hashlib.sha256(blob).hexdigest(),
                            archived_text_sha256=hashlib.sha256(raw.encode('utf-8')).hexdigest(),
                            reviewed_text_sha256=None if reviewed is None else hashlib.sha256(reviewed.encode('utf-8')).hexdigest()))
    return dict(scope='All published page records in data/index.json; exact Unicode text and the stored 29-rune alphabet. No image review or Unicode normalization is performed.',
                counts={kind: sum(r['layer_status'] == kind for r in records) for kind in
                        ['no-separate-reviewed-layer', 'identical-text', 'non-rune-changes-only', 'rune-stream-changed']},
                pages=records,
                limitation='A separate reviewed layer records selected changes, not full-page certification. Absence of that layer does not prove that a page is wrong or has never been inspected. Equal rune streams do not imply equal word boundaries or cipher reset behavior.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: all published transcription layers, classifications and hashes')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
