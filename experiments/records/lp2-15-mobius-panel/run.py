"""Apply the arithmetic Mobius function to the printed LP2-15 panel."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def factorize(n):
    if n < 1:
        raise ValueError('Mobius input must be positive')
    factors = []
    remainder = n
    divisor = 2
    while divisor * divisor <= remainder:
        exponent = 0
        while remainder % divisor == 0:
            remainder //= divisor
            exponent += 1
        if exponent:
            factors.append([divisor, exponent])
        divisor = 3 if divisor == 2 else divisor + 2
    if remainder > 1:
        factors.append([remainder, 1])
    return factors


def mobius(factors):
    return 0 if any(exponent > 1 for _, exponent in factors) else (-1) ** len(factors)


def run():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for item in plan['inputs']:
        if digest(ROOT / item['path']) != item['sha256']:
            raise ValueError('Archived page has changed: ' + item['path'])
    page = json.loads((ROOT / 'data/pages/lp2-15.json').read_text(encoding='utf-8'))
    numbers = page['numbers']
    assert len(numbers) == 4 and all(len(row) == 4 for row in numbers)
    cells = []
    for row, values in enumerate(numbers, start=1):
        for col, n in enumerate(values, start=1):
            factors = factorize(n)
            cells.append({'row': row, 'column': col, 'printed': n,
                          'factorization': factors, 'mobius': mobius(factors)})
    matrix = [[cells[4 * row + col]['mobius'] for col in range(4)] for row in range(4)]
    counts = {str(v): sum(cell['mobius'] == v for cell in cells) for v in (-1, 0, 1)}
    return {'schema': 'liberpedia-lp2-15-mobius-panel-v1',
            'plan_sha256': digest(HERE / 'plan.json'),
            'page': page['id'], 'image_sha256': page['image_sha256'],
            'numbers': numbers, 'cells': cells, 'mobius_matrix': matrix, 'counts': counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
        if result != saved:
            raise SystemExit('Stored result differs from recomputation')
        print('All 16 printed values and Möbius outputs reproduce.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, ensure_ascii=True, indent=2)
            handle.write('\n')
    print('Rows:', result['mobius_matrix'], 'counts:', result['counts'])


if __name__ == '__main__':
    main()
