"""Compare saved shuffle models without running a new statistical test."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
base=json.loads((HERE.parent/'lp2-31-periodic-ioc/results.json').read_text(encoding='utf-8'))
variant=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
assert base['observed']==variant['observed']
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 430" role="img" aria-labelledby="title desc"><title id="title">Same score, two shuffle rules</title><desc id="desc">The observed period-13 score remains 216 divided by 5300. Whole-page shuffling has 213 of 999 maxima at least as large, corrected p 0.214. Within-row shuffling has 245 of 999, corrected p 0.246. Neither is below 0.05.</desc><rect width="360" height="430" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48"><text x="20" y="32" font-size="20">Same score, two shuffle rules</text><text x="20" y="60" font-size="14">Observed peak: period 13, IoC 0.04075</text><text x="20" y="82" font-size="13">Periods 2–20 · maximum compared with maximum</text>']
for i,(name,r,color) in enumerate([('Whole page',base,'#416879'),('Within each archived row',variant,'#6c604b')]):
    y=122+i*108;n=len(r['null_trials']);count=r['exceedances']
    parts.append(f'<text x="20" y="{y}" font-size="17">{name}</text><rect x="20" y="{y+14}" width="300" height="22" fill="#e3e6e5"/><rect x="20" y="{y+14}" width="{300*count/n:.3f}" height="22" fill="{color}"/><text x="20" y="{y+56}" font-size="14">{count} of {n} shuffled maxima ≥ observed</text><text x="20" y="{y+77}" font-size="14">Corrected Monte Carlo p = {r["monte_carlo_p"]:.3f}</text>')
parts.append('<path d="M20 333 H340" stroke="#bec8ca"/><text x="20" y="357" font-size="13">Each full bar represents all 999 shuffles.</text><text x="20" y="380" font-size="13">Neither result meets the 0.05 threshold.</text><text x="20" y="403" font-size="13">This does not rule out periodic structure.</text></g></svg>')
(HERE/'comparison.svg').write_text(''.join(parts)+'\n',encoding='utf-8',newline='\n')
