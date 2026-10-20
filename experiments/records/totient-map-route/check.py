"""Independent arithmetic check using prime-factor totients and direct row assertions."""
import json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def factors(n):
    out={};p=2
    while n>1:
        while n%p==0:out[p]=out.get(p,0)+1;n//=p
        p+=1
    return out
def phi(n):
    result=n
    for p in factors(n):result=result//p*(p-1)
    return result
def mu(n):
    f=factors(n)
    return 0 if any(v>1 for v in f.values()) else (-1)**len(f)
d=json.loads((HERE/'route.json').read_text(encoding='utf-8'));g=d['map_indices'];count=0
for b in d['blocks']:
    node=[g[(r-1)*27+c-1] for r,c in [b['node_outer_cells'][0],b['node_center'],b['node_outer_cells'][1]]]
    key=[node[0],phi(node[1]) if b['center_transform'] else node[1],node[2]]
    assert key==b['key']
    phase=sum(mu(phi(v)) for v in key)%3
    for i,row in enumerate(b['rows']):
        r,c=row['cell'];cipher=g[(r-1)*27+c-1];k=key[(i+phase)%3]
        assert cipher==row['cipher'] and k==row['aligned_key'] and (cipher-k)%29==row['plaintext'];count+=1
# Exhaustive positive-index phi check against coprime counting, including phi(1).
for n in range(1,730):assert phi(n)==sum(math.gcd(n,k)==1 for k in range(1,n+1))
assert mu(1)==1 and mu(4)==0 and mu(6)==1 and mu(30)==-1
print(f'PASS: {len(d["blocks"])} selected blocks, {count} rune subtractions, key-node derivation, 729 totient controls')

# Recompute transitions from the input route, using coordinate rotations instead
# of the production script's closed-form rotated-position expressions.
def rotate(cell, turns):
    row, column = cell
    for _ in range(turns):
        row, column = column, 28 - row
    return row, column


def position(cell):
    return (cell[0] - 1) * 27 + cell[1]


report = json.loads((ROOT / 'exports/totient-map-route.json').read_text(encoding='utf-8'))
primary = [block for block in d['blocks'] if block['primary']]
assert len(report['transitions']) == len(primary) - 1 == 16
phase_total = 0
outer_state = 0
for current, following, saved in zip(primary, primary[1:], report['transitions']):
    cells = [row['cell'] for row in current['rows']]
    next_cells = [row['cell'] for row in following['rows']]
    center = current['node_center']
    original_index = g[position(center) - 1]
    reflected = 7 <= phase_total < 21
    offset = int(phase_total < 7 or 14 <= phase_total < 21)
    transformed = [position(rotate(cell, 2 if reflected else 0)) for cell in cells]
    mobius_values = [mu(value) for value in transformed]
    phase = (sum(mobius_values) + offset) % 3
    quarter_turns = [position(rotate(cell, 1)) for cell in cells]
    minimum = min(quarter_turns)
    before = outer_state
    outer_state = (outer_state + mu(minimum)) % 2
    middle = (phase - 2 * outer_state) % 3
    signature = [outer_state, {0: 0, 1: 1, 2: -1}[middle], outer_state]
    observed = [mu(phi(index)) for index in following['key']]
    assert signature == observed == saved['predicted_signature'] == saved['observed_signature']

    reflected_start = position(rotate(cells[0], 2))
    reflected_end = position(rotate(cells[-1], 2))
    turned_end = position(rotate(cells[-1], 1))
    argument = reflected_start + position(center)
    divisor = math.gcd(turned_end, reflected_end)
    terms = [mu(argument), mu(divisor)]
    score = sum(terms)
    predicted_axis = 'horizontal' if score == 0 else 'vertical' if score > 0 else 'diagonal'
    first, last = next_cells[0], next_cells[-1]
    actual_axis = 'horizontal' if first[0] == last[0] else 'vertical' if first[1] == last[1] else 'diagonal'
    assert predicted_axis == actual_axis == saved['predicted_axis'] == saved['observed_axis']

    three_quarters = position(rotate(cells[-1], 3))
    boundary = (mu(three_quarters) + phi(original_index)) % 2
    selected = min(next_cells, key=lambda cell: position(rotate(cell, 1)))
    assert selected in (first, last), 'Boundary must be an endpoint, not an interior cell'
    actual_boundary = int(selected == first)
    assert boundary == actual_boundary == saved['predicted_boundary'] == saved['observed_boundary']

    expected_ledger = {
        'current_cells': cells,
        'original_node_center': center,
        'original_center_index': original_index,
        'phase': {
            'positions': [position(cell) for cell in cells],
            'transformed_positions': transformed,
            'mobius_values': mobius_values,
            'offset': offset,
            'result': phase,
            'cumulative_after': phase_total + phase,
        },
        'outer_state': {
            'before': before,
            'quarter_turned_positions': quarter_turns,
            'minimum': minimum,
            'mobius_at_minimum': mu(minimum),
            'after': outer_state,
        },
        'axis': {
            'reflected_beginning': reflected_start,
            'node_position': position(center),
            'sum_argument': argument,
            'quarter_turned_endpoint': turned_end,
            'reflected_endpoint': reflected_end,
            'gcd': divisor,
            'mobius_terms': terms,
        },
        'boundary': {
            'three_quarter_turned_endpoint': three_quarters,
            'endpoint_mobius': mu(three_quarters),
            'center_totient': phi(original_index),
            'next_cells': next_cells,
            'selected_next_cell': selected,
            'encoding': '1 = beginning, 0 = end',
        },
    }
    assert saved['calculation'] == expected_ledger, current['label']
    assert saved['cumulative_before'] == phase_total
    assert saved['axis_score'] == score
    assert all(saved[field] for field in ('signature_match', 'axis_match', 'boundary_match'))
    phase_total += phase

# Exact geometric controls: each documented key center is its endpoints' midpoint.
for block in d['blocks']:
    left, right = block['node_outer_cells']
    center = block['node_center']
    assert all(left[axis] + right[axis] == 2 * center[axis] for axis in (0, 1))
for row in range(1, 28):
    for column in range(1, 28):
        cell = (row, column)
        assert rotate(cell, 4) == cell
        assert position(cell) + position(rotate(cell, 2)) == 730
print('PASS: all 16 transition ledgers, 18 node midpoints and 729 rotation controls')
