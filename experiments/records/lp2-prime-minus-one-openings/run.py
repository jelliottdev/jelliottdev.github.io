"""Bounded prime-minus-one opening search. Python standard library only."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shifts(count):
    """Sieve enough primes, then return p_1 - 1, p_2 - 1, ..."""
    limit = 32
    while True:
        flags = bytearray(b'\1') * (limit + 1)
        flags[:2] = b'\0\0'
        for n in range(2, int(limit ** 0.5) + 1):
            if flags[n]:
                flags[n*n:limit+1:n] = b'\0' * len(range(n*n, limit+1, n))
        primes = [n for n in range(2, limit+1) if flags[n]]
        if len(primes) >= count:
            return [p-1 for p in primes[:count]]
        limit *= 2


def run():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for entry in plan['inputs']:
        if digest(ROOT / entry['path']) != entry['sha256']:
            raise ValueError('Input changed: ' + entry['path'])
    alphabet = [r['rune'] for r in json.loads(
        (ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']]
    lookup = {r: i for i, r in enumerate(alphabet)}
    assert len(lookup) == 29
    streams = {}
    for page in plan['pages']:
        text = (ROOT / 'text' / (page + '.txt')).read_text(encoding='utf-8')
        if {c for c in text if '\u16a0' <= c <= '\u16ff'} - set(alphabet):
            raise ValueError('Unrecognized rune: ' + page)
        streams[page] = [lookup[c] for c in text if c in lookup]
    key = shifts(max(map(len, streams.values())) + max(plan['offsets']))
    cases = []
    for page, stream in streams.items():
        if not stream:
            continue
        for offset in plan['offsets']:
            for sign in plan['signs']:
                output = [(c + sign * key[j+offset]) % 29
                          for j, c in enumerate(stream)]
                matches = [o['id'] for o in plan['openings']
                           if output[:plan['prefix_length']] == o['indices']]
                cases.append(dict(page=page, offset=offset, sign=sign,
                                  output_indices=output, matching_openings=matches))
    return dict(schema='liberpedia-prime-minus-one-openings-v1',
                plan_sha256=digest(HERE / 'plan.json'), shifts=key,
                page_lengths={p: len(s) for p, s in streams.items()},
                empty_pages=[p for p, s in streams.items() if not s],
                case_count=len(cases),
                comparison_count=len(cases) * len(plan['openings']),
                matching_case_count=sum(bool(c['matching_openings']) for c in cases),
                cases=cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE / 'results.json').read_text(encoding='utf-8')):
            raise SystemExit('Rerun differs from stored results')
        print('Every candidate and match decision reproduces exactly.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(result, f, ensure_ascii=True, separators=(',', ':'))
            f.write('\n')
    print(json.dumps({k: result[k] for k in
                      ('case_count', 'comparison_count', 'matching_case_count', 'empty_pages')}))


if __name__ == '__main__':
    main()
