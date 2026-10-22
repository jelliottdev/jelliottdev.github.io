"""Check a reported Mobius-of-totient zero constraint on solved LP2-56."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mobius(n):
    factors = 0
    p = 2
    while p * p <= n:
        if n % p == 0:
            n //= p
            factors += 1
            if n % p == 0:
                return 0
        p += 1
    if n > 1:
        factors += 1
    return -1 if factors % 2 else 1


def run():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for entry in plan['inputs']:
        if digest(ROOT / entry['path']) != entry['sha256']:
            raise ValueError('Input changed: ' + entry['path'])
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    page = json.loads((ROOT / 'data/pages/lp2-56.json').read_text(encoding='utf-8'))
    by_rune = {item['rune']: item['index'] for item in alphabet}
    assert len(alphabet) == 29 and len(by_rune) == 29
    zero = [mobius(item['prime'] - 1) == 0 for item in alphabet]
    ciphertext = [by_rune[r] for r in page['raw'] if r in by_rune]
    unknown = {r for r in page['raw'] if '\u16a0' <= r <= '\u16ff'} - set(by_rune)
    if unknown:
        raise ValueError('Unrecognized manuscript rune')
    # Published LP2-56 reading uses plaintext index = ciphertext index - 1 mod 29.
    shifts = []
    for shift in range(29):
        plaintext = [(c - shift) % 29 for c in ciphertext]
        c_zero_p_nonzero = [i for i, (c, p) in enumerate(zip(ciphertext, plaintext))
                             if zero[c] and not zero[p]]
        c_nonzero_p_zero = [i for i, (c, p) in enumerate(zip(ciphertext, plaintext))
                             if not zero[c] and zero[p]]
        shifts.append(dict(shift=shift, cipher_zero_plain_nonzero=c_zero_p_nonzero,
                           cipher_nonzero_plain_zero=c_nonzero_p_zero,
                           total_mismatch=len(c_zero_p_nonzero) + len(c_nonzero_p_zero)))
    return dict(schema='liberpedia-mobius-zero-mask-known-page-v1',
                plan_sha256=digest(HERE / 'plan.json'), page='lp2-56',
                rune_count=len(ciphertext),
                alphabet=[dict(index=item['index'], latin=item['latin'], prime=item['prime'],
                               totient=item['prime'] - 1, mobius=mobius(item['prime'] - 1))
                          for item in alphabet],
                ciphertext_indices=ciphertext, shifts=shifts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE / 'results.json').read_text(encoding='utf-8')):
            raise SystemExit('Stored output differs from rerun')
        print('All 29 shifts and mismatch positions reproduce exactly.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as out:
            json.dump(result, out, ensure_ascii=True, separators=(',', ':'))
            out.write('\n')
    actual = result['shifts'][1]
    print(json.dumps(dict(runes=result['rune_count'],
                          cipher_zero_plain_nonzero=len(actual['cipher_zero_plain_nonzero']),
                          cipher_nonzero_plain_zero=len(actual['cipher_nonzero_plain_zero']),
                          total_mismatch=actual['total_mismatch'])))


if __name__ == '__main__':
    main()
