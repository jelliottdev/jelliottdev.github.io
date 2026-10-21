"""Generate a saved-result comparison figure; no extraction or inferred plaintext."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'results/comparison.json').read_bytes())
groups = [('Successful exit', '0 -> 0', '#31596b'),
          ('Existing rejection', '1 -> 1', '#85817a'),
          ('Abnormal exit → explicit guard', '3221225620 -> 1', '#996b36')]
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="400" viewBox="0 0 720 400" role="img" aria-labelledby="title desc">',
         '<title id="title">OutGuess: baseline compared with the guarded build</title>',
         '<desc id="desc">31 successful exits remain successful, five rejections remain rejections, and 41 abnormal exits become explicit guard rejections. All 77 output byte streams remain identical. Successful exit does not authenticate a payload.</desc>',
         '<rect width="720" height="400" fill="#faf9f5"/>',
         '<g font-family="sans-serif" fill="#222">',
         '<text x="24" y="35" font-size="23">Same inputs, clearer failure diagnostics</text>',
         '<text x="24" y="62" font-size="16">77 original JPEGs · default key · recorded Windows builds</text>']
for index, (label, pair, color) in enumerate(groups):
    count = report['returncode_pairs'][pair]
    y = 102 + index*74
    parts.append(f'<text x="24" y="{y}" font-size="17">{label}</text>')
    parts.append(f'<rect x="24" y="{y+10}" width="{count*12}" height="23" fill="{color}"/>')
    parts.append(f'<text x="{34+count*12}" y="{y+28}" font-size="17">{count}</text>')
parts.extend([f'<text x="24" y="331" font-size="18">{report["same_payload_bytes"]}/77 output byte streams unchanged</text>',
              '<text x="24" y="359" font-size="16">Ten are known controls; other output remains unverified.</text>',
              '<text x="24" y="383" font-size="16">A guard rejection does not establish absence of hidden data.</text>', '</g></svg>'])
(HERE/'results/comparison.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8', newline='\n')
