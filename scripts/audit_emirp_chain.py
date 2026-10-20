"""Reproduce the proposed Unicode/emirp chain and a finite reference count.

This is an arithmetic audit, not a probability model or manuscript decryption.
Python standard library only; no network requests.
"""
import argparse
import json
from math import isqrt
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def reverse(n):
    return int(str(n)[::-1])


def emirp(n):
    return n != reverse(n) and prime(n) and prime(reverse(n))


def report():
    primes = [n for n in range(2, 110000) if prime(n)]
    assert len(primes) >= 9999
    population = [n for n in range(1000, 10000) if emirp(n)]
    records = [{"emirp": n, "nth_prime": primes[n-1],
                "nth_prime_is_emirp": emirp(primes[n-1])} for n in population]
    matches = sum(r["nth_prime_is_emirp"] for r in records)
    value = ord('\u221e')
    width = value.bit_length()
    complement = ((1 << width) - 1) ^ value
    assert (value, width, complement, reverse(complement)) == (8734, 14, 7649, 9467)
    assert (len(records), matches) == (204, 67)
    return {
        "schema": "liberpedia-emirp-chain-v1",
        "binary": {"value": value, "width": width, "bits": format(value, '014b'),
                   "complement": complement, "complement_bits": format(complement, '014b'),
                   "sixteen_bit_complement": ((1 << 16) - 1) ^ value},
        "unicode": [{"decimal": n, "code_point": f"U+{n:04X}",
                     "name": unicodedata.name(chr(n))} for n in (8734, 7649, 9467)],
        "chain": {"reversed_complement": reverse(complement),
                  "p_9467": primes[9466], "p_3299": primes[3298],
                  "product": primes[9466] * primes[3298]},
        "reference_population": "All decimal emirps from 1000 through 9999 inclusive; palindromic primes excluded; each value counted, not reversal pairs",
        "population_count": len(records), "matching_count": matches,
        "proportion": matches / len(records),
        "limits": "Finite descriptive proportion, not the chance probability of the selected chain or evidence for a manuscript relationship",
        "records": records,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((ROOT/'exports/emirp-chain-audit.json').read_text(encoding='utf-8'))
        print('PASS: binary width, Unicode names, prime lookups and all 204 reference cases')
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, indent=2)
            handle.write('\n')
    if not args.check and not args.output:
        print(json.dumps(result, indent=2))
