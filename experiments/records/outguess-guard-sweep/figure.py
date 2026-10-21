"""Generate a saved-result comparison figure; no extraction or inferred plaintext."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'results/comparison.json').read_bytes())
groups = [('Successful exit', '0 -> 0', '#31596b'),
          ('Existing rejection', '1 -> 1', '#85817a'),
          ('Abnormal exit → guard', '3221225620 -> 1', '#996b36')]
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="430" viewBox="0 0 480 430" role="img" aria-labelledby="title desc">',
         '<title id="title">OutGuess: baseline compared with the guarded build</title>',
         '<desc id="desc">31 successful exits remain successful, five rejections remain rejections, and 41 abnormal exits become explicit guard rejections. All 77 output byte streams remain identical. Successful exit does not authenticate a payload.</desc>',
         '<rect width="480" height="430" fill="#faf9f5"/>',
         '<g font-family="sans-serif" fill="#222">',
         '<text x="24" y="35" font-size="23">OutGuess build comparison</text>',
         '<text x="24" y="62" font-size="19">77 original JPEGs · same default key</text>']
for index, (label, pair, color) in enumerate(groups):
    count = report['returncode_pairs'][pair]
    y = 102 + index*74
    parts.append(f'<text x="24" y="{y}" font-size="20">{label}</text>')
    parts.append(f'<rect x="24" y="{y+10}" width="{count*9}" height="23" fill="{color}"/>')
    parts.append(f'<text x="{34+count*9}" y="{y+28}" font-size="20">{count}</text>')
parts.extend([f'<text x="24" y="331" font-size="21">{report["same_payload_bytes"]}/77 output byte streams unchanged</text>',
              '<text x="24" y="359" font-size="19">Ten controls; other output unverified.</text>',
              '<text x="24" y="383" font-size="19">Rejection does not rule out hidden data.</text>', '</g></svg>'])
(HERE/'results/comparison.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8', newline='\n')
