"""Render observed scores from results.json; no new experiment is run."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
r = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 670" role="img" aria-labelledby="title desc"><title id="title">LP2-31 pooled column IoC</title><desc id="desc">Observed periods 2 to 20. Period 13 is highest at 0.04075. This peak is not significant against the scanned shuffle maxima: p equals 0.214.</desc><rect width="360" height="670" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48"><text x="20" y="30" font-size="19">LP2-31: observed period scan</text><text x="20" y="54" font-size="13">269 runes · pooled column IoC</text>']
for i, row in enumerate(r['observed']):
    y = 84 + i * 26
    score = row['pooled_ioc']
    color = '#a35328' if row['period'] in r['best_periods'] else '#416879'
    parts.append(f'<text x="20" y="{y+13}" font-size="13">{row["period"]}</text><rect x="50" y="{y}" width="{score/.05*220:.3f}" height="17" fill="{color}"/><text x="280" y="{y+13}" font-size="12">{score:.5f}</text>')
parts.append('<text x="20" y="601" font-size="14">Period 13 is the largest observed score.</text><text x="20" y="624" font-size="14">213 / 999 shuffled maxima ≥ this peak.</text><text x="20" y="647" font-size="14">Corrected p = 0.214; threshold = 0.05.</text></g></svg>')
(HERE / 'period-scan.svg').write_text(''.join(parts)+'\n', encoding='utf-8', newline='\n')
