"""Mobile figure exposing which source entropy numbers share a model."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make():
    d = json.loads((HERE / 'source-results.json').read_text(encoding='utf-8'))
    hp = d['H_P']['total_bits']
    hc = d['H_C']['filtered_bits']
    pad = hp + d['budgets'][0]['H_K_bits']
    seeded = hp + d['budgets'][2]['H_K_bits']
    x0, width = 16, 287
    xx = lambda v: x0 + width * v / 105000
    dash = xx(hc)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 306" role="img" aria-labelledby="title desc">',
           '<title id="title">The budget mixes output and key models</title>',
           '<desc id="desc">The source estimates 62.6 thousand ciphertext bits under its full random-pad law. Its English proxy plus full random pad is 98 thousand bits. Replacing the pad with only a 256-bit seed gives a 33.5-thousand-bit input proxy, yet the source reuses the same 62.6-thousand-bit output entropy. Without additional randomness those numbers cannot describe one deterministic model.</desc>',
           '<rect width="320" height="306" fill="#f7f8fa"/>',
           '<text x="16" y="27" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202c34">The entropy model changes</text>',
           '<text x="16" y="49" font-family="Arial,sans-serif" font-size="13" fill="#52636e">English proxy + key · thousands of bits</text>',
           f'<line x1="{dash:.1f}" y1="67" x2="{dash:.1f}" y2="211" stroke="#117491" stroke-width="2" stroke-dasharray="4 3"/>',
           '<text x="16" y="88" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#26333c">Full random pad</text>',
           f'<rect x="{x0}" y="100" width="{xx(pad)-x0:.1f}" height="20" fill="#496b7c"/>',
           f'<text x="{x0}" y="139" font-family="Arial,sans-serif" font-size="13" fill="#52636e">Input proxy: {pad/1000:.1f}k</text>',
           '<text x="16" y="172" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#26333c">256-bit seed</text>',
           f'<rect x="{x0}" y="184" width="{xx(seeded)-x0:.1f}" height="20" fill="#a36b5c"/>',
           f'<text x="{x0}" y="225" font-family="Arial,sans-serif" font-size="13" fill="#52636e">Input proxy: {seeded/1000:.1f}k</text>',
           f'<text x="16" y="257" font-family="Arial,sans-serif" font-size="13" fill="#117491">Dashed: source output estimate {hc/1000:.1f}k</text>',
           '<text x="16" y="281" font-family="Arial,sans-serif" font-size="13" fill="#52636e">The seed row needs a new output law</text>',
           '<text x="16" y="299" font-family="Arial,sans-serif" font-size="13" fill="#52636e">or additional counted randomness.</text>',
           '</svg>']
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    file = HERE / 'budget-models.svg'
    content = make()
    if args.check:
        assert file.read_text(encoding='utf-8') == content
        print('PASS: model-comparison SVG matches pinned source numbers')
    else:
        file.write_text(content, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
