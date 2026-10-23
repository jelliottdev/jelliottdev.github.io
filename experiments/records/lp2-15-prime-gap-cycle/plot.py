"""Small responsive SVG of the failed frozen four-step prediction."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    r = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    rows = [
        ('Shown tail', r['residues_mod28'][11:15], '#2b5870'),
        ('Predicted next', r['predicted_next_eight_mod28'][:4], '#2b5870'),
        ('Actual next', r['actual_next_eight_mod28'][:4], '#a44839'),
    ]
    parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="246" viewBox="0 0 320 246" role="img" aria-labelledby="title desc">
<title id="title">The proposed modulo-28 gap cycle fails at its first prediction</title>
<desc id="desc">The shown tail is 8, 20, 10, 6. Repeating it predicts the next four residues will be 8, 20, 10, 6. The next four generated residues are 4, 2, 20, 2.</desc>
<rect width="320" height="246" fill="#f5f6f7"/>
<text x="16" y="30" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#20252a">The next gap breaks the pattern</text>
<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#4f5961">Prime gaps reduced modulo 28</text>''']
    for rownum, (label, values, color) in enumerate(rows):
        y = 72 + 54*rownum
        parts.append(f'<text x="16" y="{y+13}" font-family="Arial,sans-serif" font-size="14" fill="#30383e">{label}</text>')
        for i, value in enumerate(values):
            x = 128+44*i
            parts.append(f'<rect x="{x}" y="{y-7}" width="39" height="33" rx="4" fill="#fff" stroke="{color}" stroke-width="1.5"/>')
            parts.append(f'<text x="{x+19.5}" y="{y+15}" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="{color}">{value}</text>')
    parts.append('''<line x1="16" y1="220" x2="304" y2="220" stroke="#c4cbd0"/>
<text x="16" y="239" font-family="Arial,sans-serif" font-size="13" fill="#4f5961">First new gap: 5660 mod 28 = 4, not 8.</text>
</svg>
''')
    return ('\n'.join(parts)).encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = HERE / 'gap-cycle.svg'
    payload = render()
    if args.check:
        assert path.read_bytes() == payload
        print('SVG matches saved result.')
    else:
        path.write_bytes(payload)
        print(path)


if __name__ == '__main__':
    main()
