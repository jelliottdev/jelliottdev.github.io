"""Literal finite route operations from the pinned solve_p20.py source."""
from __future__ import annotations

from collections import Counter
from math import ceil, isqrt

LATIN = ('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S',
         'T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA')
COMMON = {'THE','AND','FOR','ING','ION','THA','ENT','HER','WAS','HIS',
          'ALL','BUT','ARE','NOT','YOU','CAN'}
COLUMN = COMMON | {'HAS','OUR','OUT'}
KEYWORDS = [('CABAL',[5,24,17,24,20]),
            ('DIVINITY',[23,10,1,10,9,10,16,26]),
            ('DEOR',[23,18,3,4]),
            ('SHADOWS',[15,8,24,23,3,7,15])]


def is_prime(n: int) -> bool:
    return n >= 2 and all(n % k for k in range(2, isqrt(n) + 1))


def ioc(values: list[int]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    freq = Counter(values)
    return 29 * sum(q * (q - 1) for q in freq.values()) / (n * (n - 1))


def latin(values: list[int]) -> str:
    return ''.join(LATIN[x] for x in values)


def trigrams(values: list[int], allowed: set[str]) -> int:
    text = latin(values)
    return sum(text[i:i+3] in allowed for i in range(len(text)-2))


def nonprime_position_stream(page: list[int]) -> list[int]:
    return [value for pos, value in enumerate(page) if not is_prime(pos)]


def _spiral(values: list[int], width: int) -> list[int]:
    n = len(values); height = ceil(n / width)
    grid = [[values[r*width+c] if r*width+c < n else 0 for c in range(width)] for r in range(height)]
    output: list[int] = []
    top, bottom, left, right = 0, height-1, 0, width-1
    while top <= bottom and left <= right:
        for c in range(left, right+1):
            if len(output) < n: output.append(grid[top][c])
        top += 1
        for r in range(top, bottom+1):
            if len(output) < n: output.append(grid[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left-1, -1):
                if len(output) < n: output.append(grid[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top-1, -1):
                if len(output) < n: output.append(grid[r][left])
            left += 1
    return output[:n]


def routes(values: list[int], deor_key: list[int]) -> list[dict]:
    n = len(values)
    output: list[dict] = []
    def add(name: str, v: list[int], gate: int | None = None, allowed=COMMON) -> None:
        tri = trigrams(v, allowed)
        output.append({'name': name, 'values': v, 'trigrams': tri,
                       'source_gate': gate, 'reported': gate is None or tri > gate,
                       'ioc': ioc(v), 'complete_permutation': len(v)==n and Counter(v)==Counter(values)})
    add('prime_positions', [values[p] for p in range(n) if is_prime(p)])
    add('reversed', values[::-1])
    for width in [2,3,5,7,11,13,17,19,23,29,31,34,37,38,41,43,47]:
        if width >= n: continue
        nrows = ceil(n / width)
        add(f'columnar_w{width}', [values[row*width+col] for col in range(width) for row in range(nrows) if row*width+col<n], 5, COLUMN)
    for width in [17,19,23,29,31,34,37,38]:
        if width >= n: continue
        nrows=ceil(n/width)
        add(f'diagonal_w{width}', [values[row*width + d-row] for d in range(width+nrows-1) for row in range(nrows)
                                     if 0 <= d-row < width and row*width+d-row<n], 5)
    for width in [17,19,23,25,26,29,34]:
        add(f'spiral_w{width}', _spiral(values, width), 5)
    add('gp_value_sorted', [values[i] for i in sorted(range(n),key=lambda i:values[i])])
    for step in [2,3,5,7,11,13]:
        for start in range(step):
            v = values[start:n:step]
            if len(v)>20:
                add(f'every_{step}th_start{start}', v, 3)
    fib = [0,1]
    while fib[-1]<n:
        fib.append(fib[-1]+fib[-2])
    add('fibonacci_positions', [values[p] for p in fib if p<n])
    for label,key in KEYWORDS:
        width=len(key); nrows=ceil(n/width)
        order=sorted(range(width),key=lambda c:key[c])
        add(f'route_{label}', [values[row*width+c] for c in order for row in range(nrows) if row*width+c<n])
    if len(deor_key)>=n:
        add('deor_transposition',[values[i] for i in sorted(range(n),key=lambda i:(deor_key[i],i))])
    return output


def source_stage(page: list[int], deor_key: list[int]) -> dict:
    prime_pos=[page[i] for i in range(len(page)) if is_prime(i)]
    nonprime=nonprime_position_stream(page)
    shift_scores=[ioc([(x-shift)%29 for x in nonprime]) for shift in range(29)]
    best_shift=max(range(29),key=lambda shift:shift_scores[shift])
    plain=[(x-best_shift)%29 for x in nonprime]
    rows=routes(plain,deor_key)
    prime_values=[x for x in page if is_prime(x)]
    nonprime_values=[x for x in page if not is_prime(x)]
    return {'prime_position_count':len(prime_pos),'nonprime_position_count':len(nonprime),
            'prime_index_value_count':len(prime_values),'nonprime_index_value_count':len(nonprime_values),
            'shift_iocs':shift_scores,'best_shift':best_shift,'nonprime_ioc':ioc(nonprime),
            'prime_value_ioc':ioc(prime_values),'nonprime_value_ioc':ioc(nonprime_values),
            'routes':rows}
