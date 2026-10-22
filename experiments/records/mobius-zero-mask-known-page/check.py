"""Independent square-divisor check of the LP2-56 actual shift."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
page = json.loads((ROOT / 'data/pages/lp2-56.json').read_text(encoding='utf-8'))
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
symbols = {entry['rune']: entry['index'] for entry in alphabet}
indices = [symbols[r] for r in page['raw'] if r in symbols]
square_divisor = lambda n: any(n % (k * k) == 0 for k in range(2, int(n ** .5) + 1))
zeros = [square_divisor(entry['prime'] - 1) for entry in alphabet]
forward = [i for i, c in enumerate(indices) if zeros[c] and not zeros[(c - 1) % 29]]
reverse = [i for i, c in enumerate(indices) if not zeros[c] and zeros[(c - 1) % 29]]
assert indices == saved['ciphertext_indices']
assert forward == saved['shifts'][1]['cipher_zero_plain_nonzero']
assert reverse == saved['shifts'][1]['cipher_nonzero_plain_zero']
assert len(forward) == 28 and len(reverse) == 22 and len(indices) == 85
print('Independent square-divisor and stream check passed: 28 + 22 mismatches.')
