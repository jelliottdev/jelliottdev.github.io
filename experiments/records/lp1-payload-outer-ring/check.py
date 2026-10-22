"""Independent source parse and oracle for the LP1 payload-border audit."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
assert result['plan_sha256'] == hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest()
for item in plan['inputs']:
    path = ROOT / item['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], path

expected_core = [[10, 12, 10], [12, 14, 12], [10, 12, 10]]
for n, expected_border in zip(range(10, 14), '3301'):
    page = f'lp1-{n:02}'
    body = (ROOT / f'exports/steganography/{page}.body.txt').read_text(encoding='ascii')
    # Require one bounded diagram and retain the original row spacing.
    candidates = re.findall(r'(?m)^([0-9])\1{15}\r?\n(?:.{16}\r?\n){5}\1{16}$', body)
    assert candidates == [expected_border], (page, candidates)
    lines = body.splitlines()
    top = expected_border * 16
    start = lines.index(top)
    block = lines[start:start + 7]
    assert block[-1] == top and all(len(line) == 16 for line in block)
    assert all(line[0] == expected_border == line[-1] for line in block)
    core_rows = [line[1:15].split() for line in (block[1], block[3], block[5])]
    core = [[int(value) for value in row] for row in core_rows]
    assert core == expected_core
    assert result['four_signed_message_diagrams'][page]['printed_lines'] == block
    assert result['four_signed_message_diagrams'][page]['interior_matrix'] == core
    metadata = json.loads((ROOT / f'data/pages/{page}.json').read_text(encoding='utf-8'))['embedded_payload']
    assert metadata['signature_valid'] is True
    assert metadata['body_sha256'] == hashlib.sha256(body.encode('ascii')).hexdigest()

assert result['interior_matrix'] == expected_core
assert result['interior_row_sums'] == [32, 38, 32]
assert result['border_sequence'] == '3301'
alternate = result['alternative_visible_five_by_five_interpretation']
assert alternate['lp1-05_inner_3x3'] == [[199, 130, 320], [245, 91, 245], [320, 130, 199]]
assert alternate['lp1-16_inner_3x3'] == [[812, 934, 280], [620, 809, 620], [280, 934, 812]]
assert alternate['same_inner_grid'] is False
assert alternate['shared_inner_values'] == []
print('PASS: four exact ASCII diagrams, 3-3-0-1 borders and common nonmagic core; excluded 5x5 reading checked')
