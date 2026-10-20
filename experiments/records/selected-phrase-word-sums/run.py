"""Enumerate exact-label segmentations for the fixed supplied candidate list."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def report():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    labels = {a['latin']: a for a in alphabet}
    assert len(labels) == 29

    def parse(word):
        if not word:
            yield []
        for label in labels:
            if word.startswith(label):
                for tail in parse(word[len(label):]):
                    yield [label] + tail

    rows = []
    for word, target in plan['candidates']:
        normalized = word.upper().replace('V', 'U')
        variants = []
        for tokens in parse(normalized):
            values = [labels[t]['prime'] for t in tokens]
            variants.append({'labels': tokens, 'values': values,
                             'sum': sum(values), 'matches_target': sum(values) == target})
        rows.append({'word': word, 'normalized': normalized, 'target': target,
                     'variants': variants})
    return {'scope': plan, 'alphabet_sha256': hashlib.sha256((ROOT / 'data/index.json').read_bytes()).hexdigest(),
            'candidate_count': len(rows), 'segmentation_count': sum(len(r['variants']) for r in rows),
            'matching_candidates': sum(any(v['matches_target'] for v in r['variants']) for r in rows),
            'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
        print('PASS: every candidate and segmentation reproduced')
    else:
        print(json.dumps(result, ensure_ascii=True, indent=2))
