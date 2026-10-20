"""Exhaustive fixed-alphabet transformations against one declared opening.

Python 3.12 standard library. --check reproduces all candidate outputs.
--output writes a new report and refuses to overwrite an existing file.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def run():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    alphabet = [a['rune'] for a in json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']]
    assert len(set(alphabet)) == 29
    lookup = {r: i for i, r in enumerate(alphabet)}
    inputs = []
    def read(page):
        path = ROOT / 'text' / (page + '.txt')
        data = path.read_bytes()
        inputs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(data).hexdigest()})
        text = data.decode('utf-8')
        if {c for c in text if '\u16a0' <= c <= '\u16ff'} - set(alphabet):
            raise ValueError('Unknown rune in ' + page)
        return [lookup[c] for c in text if c in lookup]
    reference = read(plan['reference'])
    expected = [(28-i) % 29 for i in reference[:plan['prefix_length']]]
    assert len(expected) == plan['prefix_length']
    cases = []
    for page in plan['pages']:
        stream = read(page)
        for order in plan['orders']:
            source = stream if order == 'original' else stream[::-1]
            for multiplier in plan['multipliers']:
                for offset in plan['offsets']:
                    output = [(multiplier * i + offset) % 29 for i in source]
                    cases.append({'page': page, 'order': order, 'multiplier': multiplier,
                                  'offset': offset, 'output_indices': output,
                                  'matches_prefix': output[:len(expected)] == expected})
    return {'schema': 'liberpedia-alphabet-prefix-v1', 'plan_sha256': hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'alphabet': alphabet, 'inputs': inputs, 'expected_prefix': expected,
            'case_count': len(cases), 'match_count': sum(c['matches_prefix'] for c in cases), 'cases': cases}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE/'results.json').read_text(encoding='utf-8')):
            raise SystemExit('Stored result differs from the complete rerun')
        print('All candidate sequences and input hashes reproduce exactly.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, ensure_ascii=True, separators=(',', ':'))
            handle.write('\n')
    print(json.dumps({k: result[k] for k in ('case_count','match_count')}))

if __name__ == '__main__':
    main()
