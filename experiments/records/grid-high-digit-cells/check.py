"""Independent deterministic recount of marked LP2 grid cells."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
records = json.loads((ROOT / 'exports/alphanumeric-grids.json').read_text(encoding='utf-8'))['records']
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
marked = [(row, col, records[8 * row + col]['token'][1])
          for row in range(32) for col in range(8)
          if records[8 * row + col]['token'].startswith('4')]
assert len(marked) == 17
assert [8 * row + col for row, col, _ in marked] == saved['positions_zero_based']
assert ''.join(suffix for _, _, suffix in marked) == saved['suffix_sequence']
assert len({suffix for _, _, suffix in marked}) == 11
assert {suffix for _, _, suffix in marked} == set('056789ABDEF')
blocks = [sum(start <= row < start + 8 for row, _, _ in marked)
          for start in (0, 8, 16, 24)]
assert blocks == saved['block_counts'] == [4, 2, 9, 2]
occupied = {(row, col) for row, col, _ in marked}
touching = sum(((row + 1, col) in occupied) + ((row, col + 1) in occupied)
               for row, col in occupied)
assert touching == saved['touching_pairs'] == 7
assert saved['byte_maximum_suffix_digit'] == 15
assert saved['missing_hex_suffixes'] == '1234C'
print('PASS independent grid-high-digit-cells recount')
