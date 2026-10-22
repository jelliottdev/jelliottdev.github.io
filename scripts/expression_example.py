"""Enumerate a small arithmetic grammar using 2, 3 and 5 once each."""
from collections import defaultdict
from itertools import permutations, product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def build():
    operators = {'+': lambda a, b: a+b, '*': lambda a, b: a*b}
    outputs = defaultdict(list)
    for a, b, c in permutations([2, 3, 5]):
        for first, second in product(operators, repeat=2):
            left = operators[second](operators[first](a, b), c)
            right = operators[first](a, operators[second](b, c))
            outputs[left].append(f'(({a}{first}{b}){second}{c})')
            outputs[right].append(f'({a}{first}({b}{second}{c}))')
    counts = {value: len(expressions) for value, expressions in sorted(outputs.items())}
    assert counts == {10: 12, 11: 4, 13: 4, 16: 4, 17: 4, 21: 4, 25: 4, 30: 12}
    assert sum(counts.values()) == 48
    assert len({expression for expressions in outputs.values() for expression in expressions}) == 48
    report = dict(scope='Invented finite grammar demonstration; no manuscript claim.',
                  inputs=[2, 3, 5], operators=list(operators),
                  rules='Use each input exactly once; all orders; two binary-tree shapes; no other constants or operations.',
                  expression_count=48, distinct_output_count=len(outputs),
                  results=[dict(value=value, count=counts[value], expressions=outputs[value])
                           for value in sorted(outputs)])
    (ROOT/'exports/expression-example.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('Verified 48 distinct expression strings producing 8 distinct values.')


if __name__ == '__main__':
    build()
