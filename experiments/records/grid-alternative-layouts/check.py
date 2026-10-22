"""Independent recount of directional prime paths after row-major reshaping."""
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[3]
saved = json.loads((Path(__file__).parent / 'results.json').read_text(encoding='utf-8'))
source = json.loads((root / 'exports/alphanumeric-grids.json').read_text(encoding='utf-8'))['records']
digits = ''.join(item['token'][0] for item in source)
assert len(digits) == 256

for name, width, block in [('source_32x8', 8, 0), ('reshaped_16x16', 16, 0), ('four_8x8_quadrants', 16, 8)]:
    height = 256 // width
    frequencies = {}
    total = eligible = 0
    # Endpoint-pair enumeration differs from run.py's start-and-direction loop.
    for begin in range(256):
        y, x = divmod(begin, width)
        for end in range(256):
            ey, ex = divmod(end, width)
            dy, dx = ey - y, ex - x
            if max(abs(dx), abs(dy)) != 3 or not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                continue
            step_y, step_x = dy // 3, dx // 3
            if block and (x // block, y // block) != (ex // block, ey // block):
                continue
            total += 1
            value = ''.join(digits[(y + k * step_y) * width + x + k * step_x] for k in range(4))
            if '4' in value:
                continue
            eligible += 1
            n = int(value)
            if n >= 2 and all(n % divisor for divisor in range(2, math.isqrt(n) + 1)):
                frequencies[n] = frequencies.get(n, 0) + 1
    row = saved['observed'][name]
    assert total == row['directed_paths']
    assert eligible == row['eligible_paths']
    assert sum(frequencies.values()) == row['prime_occurrences']
    assert len(frequencies) == row['distinct_prime_values']
    assert {str(t): frequencies.get(t, 0) for t in saved['named_targets']} == row['target_occurrences']
print('PASS independent endpoint recount for all three layouts')
