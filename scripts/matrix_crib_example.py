"""Enumerate keys for invented block pairs; no manuscript inputs or cipher claim."""
from itertools import product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MOD = 29


def apply(key, block):
    a, b, c, d = key
    x, y = block
    return [(a*x+b*y) % MOD, (c*x+d*y) % MOD]


def build():
    key = (1, 2, 3, 5)
    inverse = (24, 2, 3, 28)
    for block in product(range(MOD), repeat=2):
        assert apply(inverse, apply(key, block)) == list(block)
        assert apply(key, apply(inverse, block)) == list(block)
    plain, cipher = [4, 7], [18, 18]
    assert apply(key, plain) == cipher
    matches = []
    # Each first-column choice fixes the second column through the known pair.
    for a, c in product(range(MOD), repeat=2):
        b = ((18 - 4*a)*pow(7, -1, MOD)) % MOD
        d = ((18 - 4*c)*pow(7, -1, MOD)) % MOD
        candidate = (a, b, c, d)
        assert apply(candidate, plain) == cipher
        if (a*d-b*c) % MOD:
            matches.append(candidate)
    independent = [k for k in matches if apply(k, [1, 0]) == [1, 3]]
    dependent = [k for k in matches if apply(k, [8, 14]) == [7, 7]]
    assert len(matches) == 29*28 == 812
    assert independent == [key]
    assert dependent == matches
    data = dict(scope='Synthetic linear-block illustration, not an LP test.',
                modulus=MOD, orientation='column vectors; ciphertext = matrix × plaintext',
                key=list(key), inverse=list(inverse), round_trip_blocks=29**2,
                constraints=[dict(plaintext=plain, ciphertext=cipher, reversible_keys=812),
                             dict(additional_plaintext=[8, 14], additional_ciphertext=[7, 7],
                                  reversible_keys=812, relationship='twice the first pair modulo 29'),
                             dict(additional_plaintext=[1, 0], additional_ciphertext=[1, 3],
                                  reversible_keys=1, relationship='independent of the first input')])
    (ROOT/'exports/matrix-crib-example.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Verified 841 round trips in both directions; crib counts 812, 812 and 1.')


if __name__ == '__main__':
    build()
