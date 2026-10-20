"""Draw the first four known-control steps from the archived CSV."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))[:4]
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 330" role="img" aria-labelledby="title desc">',
         '<title id="title">Four prime-minus-one decoding steps</title>',
         '<desc id="desc">Known LP2-56 control: subtract shifts 1, 2, 4 and 6 from indices 25, 11, 22 and 15, giving 24, 9, 18 and 9 modulo 29.</desc>',
         '<rect width="440" height="330" fill="#f7f7f3"/>',
         '<g font-family="sans-serif" fill="#263b46">',
         '<text x="20" y="33" font-size="21">Known LP2-56 opening</text>',
         '<text x="20" y="60" font-size="16">Input − (prime − 1) → output index</text>']
for i, row in enumerate(rows):
    y = 102 + 49*i
    label = row['latin']
    parts += [f'<path d="M20 {y+13}H420" stroke="#d7dddf"/>',
              f'<text x="22" y="{y}" font-size="20">{row["input_index"]} − {row["subtracted_value"]}</text>',
              f'<text x="180" y="{y}" font-size="20">→ {row["output_index"]}</text>',
              f'<text x="347" y="{y}" font-size="22" font-weight="bold">{label}</text>']
parts += ['<text x="20" y="295" font-size="16">Arithmetic is modulo 29.</text>',
          '<text x="20" y="318" font-size="15">This illustrates a control, not a new solution.</text>',
          '</g></svg>']
(HERE/'control.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8', newline='\n')
print('Wrote control.svg from the archived reading trace.')
