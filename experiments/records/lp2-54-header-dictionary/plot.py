"""Render the fixed six-way header comparison as responsive SVG."""
import argparse
from html import escape
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))['target_pair']['variants']
alphabet = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
names = 'F U TH O R C/K G W H N I J EO P X S T B E M L NG OE D A AE Y IA EA'.split()
labels = dict(zip(alphabet, names))
mode = {'ciphertext': 'Ciphertext feedback', 'plaintext': 'Plaintext feedback'}
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 464" role="img" aria-labelledby="title desc">',
         '<title id="title">LP2-54 fixed header-crib outputs</title>',
         '<desc id="desc">Six A, I, O and feedback combinations. None has a second word in the pinned eight-rune corpus.</desc>',
         '<rect width="720" height="464" fill="#f5f6f8"/>',
         '<text x="28" y="40" font-family="system-ui" font-size="22" font-weight="700" fill="#1d2732">Does the eight-rune word fit?</text>',
         '<text x="28" y="66" font-family="system-ui" font-size="14" fill="#52606c">LP2-54 red header · fixed first rune and one-step feedback</text>',
         '<line x1="28" x2="692" y1="86" y2="86" stroke="#cbd3da"/>']
for i, row in enumerate(rows):
    y = 116 + i * 47
    second = ' '.join(labels[g] for g in row['second_word'])
    parts.extend([f'<text x="28" y="{y}" font-family="system-ui" font-size="15" font-weight="700" fill="#263542">{row["first"]}</text>',
                  f'<text x="73" y="{y}" font-family="system-ui" font-size="14" fill="#263542">{mode[row["mode"]]}</text>',
                  f'<text x="300" y="{y}" font-family="system-ui" font-size="14" fill="#1d2732">{escape(second)}</text>',
                  f'<text x="613" y="{y}" font-family="system-ui" font-size="14" font-weight="700" fill="#5a6570">No match</text>',
                  f'<line x1="28" x2="692" y1="{y+12}" y2="{y+12}" stroke="#dce2e7"/>'])
parts.extend(['<text x="28" y="426" font-family="system-ui" font-size="14" fill="#40505e">19,715 eight-rune spellings checked · 2 planted controls recovered</text>',
              '<text x="28" y="447" font-family="system-ui" font-size="12" fill="#66717b">A dictionary miss only excludes these six fixed rules and this corpus.</text>', '</svg>'])
data = ('\n'.join(parts) + '\n').encode('utf-8')
parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
path = HERE / 'header-cribs.svg'
if args.check:
    if path.read_bytes() != data:
        raise SystemExit('Figure differs from saved result')
    print('OK: SVG matches saved six-way result')
else:
    path.write_bytes(data)
