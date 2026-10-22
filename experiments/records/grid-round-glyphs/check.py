"""Independently replay the 0/O coordinate census from page records."""
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
report = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx'

def value(token):
    return 60 * alphabet.index(token[0]) + alphabet.index(token[1])

found = []
sequence = 0
for page, expected_rows in ((49, 10), (50, 13), (51, 9)):
    raw = json.loads((ROOT / f'data/pages/lp2-{page:02}.json').read_text(encoding='utf-8'))['raw']
    rows = [line.rstrip('/').split('-') for line in raw.splitlines()
            if re.fullmatch(r'[A-Za-z0-9]{2}(?:-[A-Za-z0-9]{2}){7}/?', line)]
    assert len(rows) == expected_rows
    for row_number, row in enumerate(rows, 1):
        for column_number, token in enumerate(row, 1):
            sequence += 1
            if any(ch in '0O' for ch in token):
                found.append((sequence, f'lp2-{page}', row_number, column_number, token))
assert sequence == 256
assert len(found) == report['cell_count'] == 70
assert sum(token.count('0') for _, _, _, _, token in found) == report['zero_marks'] == 65
assert sum(token.count('O') for _, _, _, _, token in found) == report['capital_o_marks'] == 7

for expected, case in zip(found, report['cases']):
    seq, page, row, col, token = expected
    assert (case['sequence'], case['page'], case['row'], case['column'], case['wiki_token']) == expected
    assert case['wiki_base60'] == value(token)
    x0, y0, x1, y1 = case['crop_box_xyxy']
    assert 0 <= x0 < x1 <= 2400 and 0 <= y0 < y1 <= 3600
    assert x1 - x0 == 216 and y1 - y0 == 118
    marks = [m for m in case['round_marks']]
    assert len(marks) == token.count('0') + token.count('O')
    for mark in marks:
        pos = mark['character_index'] - 1
        assert mark['read_as'] == token[pos] and token[pos] in '0O'
        alternate = token[:pos] + ('O' if token[pos] == '0' else '0') + token[pos + 1:]
        assert mark['alternate_token'] == alternate
        assert mark['alternate_base60'] == value(alternate)
        assert mark['alternate_is_byte'] == (value(alternate) <= 255)
print('Independent page-record replay confirms 70 cells, 72 marks and all coordinate/value records.')
