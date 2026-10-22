"""Enumerate an invented five-symbol substitution model; no manuscript inputs."""
from itertools import permutations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def build():
    ciphertext = (0, 1, 0)
    cases = [
        ('No crib', []),
        ('First output 2', [(0, 2)]),
        ('First two outputs 2, 3', [(0, 2), (1, 3)]),
        ('Compatible full crib 2, 3, 2', [(0, 2), (1, 3), (2, 2)]),
        ('Contradictory full crib 2, 3, 4', [(0, 2), (1, 3), (2, 4)]),
    ]
    results = []
    for name, conditions in cases:
        keys = [key for key in permutations(range(5))
                if all(key[ciphertext[i]] == value for i, value in conditions)]
        outputs = sorted({tuple(key[x] for x in ciphertext) for key in keys})
        results.append(dict(name=name, conditions=conditions, count=len(keys),
                            keys=keys, distinct_outputs=outputs))
    assert [case['count'] for case in results] == [120, 24, 6, 6, 0]
    assert results[2]['keys'] == results[3]['keys']
    assert results[3]['distinct_outputs'] == [(2, 3, 2)]
    report = dict(scope='Toy exhaustive enumeration, not an LP experiment.',
                  alphabet=list(range(5)), ciphertext=ciphertext,
                  mapping_direction='plaintext = key[ciphertext]', cases=results)
    (ROOT/'exports/constraint-example.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('Verified all 120 permutations; surviving counts: 120, 24, 6, 6, 0.')


if __name__ == '__main__':
    build()
