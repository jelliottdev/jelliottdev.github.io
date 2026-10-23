"""Replay the two published circumference substitutions on LP2-00–55."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping(radius, rounding):
    values = range(29) if radius == 'index' else PRIMES
    operation = round if rounding == 'nearest' else math.trunc
    return [operation(2 * math.pi * r) % 29 for r in values]


def run():
    maps = {f'{radius}-{rounding}': mapping(radius, rounding)
            for radius in ('index', 'prime') for rounding in ('nearest', 'truncate')}
    pages = []
    for number in range(56):
        path = ROOT / 'text' / f'lp2-{number:02d}.txt'
        raw = path.read_text(encoding='utf-8')
        streams = {}
        for name, table in maps.items():
            transformed = ''.join(RUNES[table[RUNES.index(c)]] if c in RUNES else c
                                  for c in raw)
            streams[name] = {'first_nine_runes': ''.join(c for c in transformed if c in RUNES)[:9],
                             'output_sha256': hashlib.sha256(transformed.encode('utf-8')).hexdigest()}
        pages.append({'page': f'lp2-{number:02d}', 'input_sha256': sha(path),
                      'rune_count': sum(c in RUNES for c in raw), 'outputs': streams})
    # An elementary direct positive check from the printed page-zero prefix.
    assert pages[0]['outputs']['index-truncate']['first_nine_runes'][:4] == 'ᚹᛝᚣᛖ'
    assert pages[0]['outputs']['prime-truncate']['first_nine_runes'][0] == 'ᛉ'
    return {'schema': 'liberpedia-public-circumference-results-v1',
            'plan_sha256': sha(HERE / 'plan.json'),
            'maps': {name: {'output_indices': table, 'distinct_outputs': len(set(table)),
                            'collisions': 29 - len(set(table))}
                     for name, table in maps.items()},
            'pages': pages}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE / 'results.json').read_text(encoding='utf-8')):
            raise SystemExit('Rerun differs from results.json')
    else:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v['distinct_outputs'] for k, v in result['maps'].items()}))


if __name__ == '__main__':
    main()
