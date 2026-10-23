"""Independent seven-page window recount from page-record line transcriptions."""
import json
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
digits = {entry['rune']: len(str(entry['prime'])) for entry in alphabet}
per_page = []
for number in range(56):
    page = json.loads((ROOT / f'data/pages/lp2-{number:02}.json').read_text(encoding='utf-8'))
    per_page.append(sum(digits[char] for line in page['lines']
                        for char in line['raw'] if char in digits))
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
assert per_page == saved['page_prime_digit_counts']
independent = [sum(per_page[first:first + 7]) for first in range(50)]
assert independent == [item['prime_digits'] for item in saved['windows']]
assert [(first, isqrt(value)) for first, value in enumerate(independent)
        if isqrt(value)**2 == value] == [(16, 59)]
print('PASS independent lp2-seven-page-square-fits recount')
