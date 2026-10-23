"""Compact fact diagram for the raw-grid measurements, readable on a phone."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / 'results.json').read_text())
assert len(r['measurements']) == 7
assert not any(row['rejected_uniform_reference'] for row in r['measurements'])
assert all(3 in row['small_prime_divisors'] for row in r['integers'])
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 350" role="img" aria-labelledby="t d" font-family="Arial,sans-serif">
<title id="t">Two checks on the raw grid bytes</title>
<desc id="d">Seven byte statistics do not reject their uniform reference. All four literal integer readings have small prime factors and fail a conventional RSA modulus screen. Neither observation decrypts the grid.</desc>
<rect width="340" height="350" fill="#f5f7f8"/>
<g fill="#253641" font-size="15">
<text x="16" y="30" font-size="19" font-weight="700">Reading the grid without a key</text>
<text x="16" y="61">256 bytes, printed cells unchanged</text>
<line x1="16" y1="78" x2="324" y2="78" stroke="#cbd3d8"/>
<text x="16" y="109" font-weight="700">Byte measurements</text>
<text x="16" y="139">161 different values</text>
<text x="16" y="164">Random-block mean: 162</text>
<text x="16" y="192">0 of 7 tests reject the reference</text>
<line x1="16" y1="212" x2="324" y2="212" stroke="#cbd3d8"/>
<text x="16" y="243" font-weight="700">Literal RSA-modulus readings</text>
<text x="16" y="273">4 of 4 have small prime factors</text>
<text x="16" y="298">All four are divisible by 3 and 7</text>
<text x="16" y="333" font-size="14" fill="#52636d">These checks do not reveal a plaintext.</text>
</g></svg>
'''
p = HERE / 'byte-checks.svg'
if sys.argv[1:] == ['--check']:
    assert p.read_text(encoding='utf-8') == svg
    print('PASS: raw-grid fact diagram')
else:
    p.write_text(svg, encoding='utf-8', newline='\n')
