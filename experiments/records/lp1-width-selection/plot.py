"""Render all observed widths and the complete selected-minimum distribution."""
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def frame(height, title, description):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{title}</title><desc id="desc">{description}</desc>',
            '<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font:14px Arial,sans-serif;fill:#25343a}.small{font-size:12px}</style>']


def render():
    data = json.loads((HERE/'results.json').read_bytes())
    receipt = json.loads((HERE/'audit.json').read_bytes())
    assert receipt['status'] == 'passed'
    assert receipt['report_sha256'] == hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()
    values = [float(Fraction(v)) for v in data['observed_R']]
    parts = frame(620, 'Six widths, two different rankings', 'Width 2 minimizes normalized imbalance R. Width 32 has the smallest unadjusted fixed-width tail. These are different selection criteria.')
    parts += ['<text x="20" y="28">Six widths, two different rankings</text>',
              '<text x="20" y="51" class="small">Bars: observed R · shared scale 0–1</text>']
    for i,(width,value,p) in enumerate(zip(data['widths'],values,data['fixed_width_p'])):
        y = 82 + 76*i
        parts += [f'<text x="20" y="{y}">Width {width}</text>',
                  f'<text x="360" y="{y}" text-anchor="end">R = {value:.4f}</text>',
                  f'<rect x="20" y="{y+11}" width="340" height="14" fill="#eef1f2"/>',
                  f'<rect x="20" y="{y+11}" width="{340*value:.3f}" height="14" fill="#42687b"/>',
                  f'<text x="20" y="{y+46}" class="small">Unadjusted fixed-width tail: {float(Fraction(p)):.5f}</text>']
    parts += ['<text x="20" y="558">The frozen rule selects the smallest R.</text>',
              '<text x="20" y="583" class="small">It does not select the smallest fixed-width tail.</text>',
              '<text x="20" y="605" class="small">The six tail estimates are not adjusted or independent.</text>', '</svg>']
    minima = [Fraction(a,b) for a,b in data['null_minima']]
    bins = 30
    step = Fraction((int(max(minima)*10)//3+1)*3, 10*bins)
    counts = [0]*bins
    for value in minima: counts[min(int(value/step),bins-1)] += 1
    assert sum(counts) == 49999
    table = io.StringIO(newline='')
    writer = csv.writer(table,lineterminator='\n')
    writer.writerow(['left_inclusive','right_exclusive','count'])
    for i,count in enumerate(counts):writer.writerow([str(i*step),str((i+1)*step),count])
    xmax = float(step*bins)
    highest = max(counts)
    s = frame(420,'Minimum R after searching every width','All 49999 controls search the same six widths. 6035 control minima are no greater than the observed minimum, giving a plus-one tail of 0.12072.')
    s += ['<text x="20" y="28">Every control searches all six widths</text>',
          '<text x="20" y="51" class="small">49,999 shuffled minima · bar height counts controls</text>']
    for i,count in enumerate(counts):
        height = 215*count/highest
        s.append(f'<rect x="{48+310*i/bins:.3f}" y="{290-height:.3f}" width="{310/bins-1:.3f}" height="{height:.3f}" fill="#42687b"/>')
    observed = float(Fraction(*data['observed_minimum']))
    marker = 48 + 310*observed/xmax
    s += [f'<path d="M{marker:.3f} 70 V290" stroke="#9a5526" stroke-width="2" stroke-dasharray="5 4"/>',
          '<path d="M48 70 V290 H358" stroke="#70808a" fill="none"/>',
          '<text x="40" y="294" text-anchor="end" class="small">0</text>',
          f'<text x="40" y="80" text-anchor="end" class="small">{highest:,}</text>',
          '<text x="48" y="312" class="small">0</text>',
          f'<text x="358" y="312" text-anchor="end" class="small">{xmax:.1f}</text>',
          '<text x="203" y="335" text-anchor="middle">Minimum R</text>',
          f'<text x="20" y="365" class="small">Dashed line: observed R = {observed:.5f}</text>',
          '<text x="20" y="388">6,035 / 49,999 at or below the observation</text>',
          '<text x="20" y="410" class="small">Plus-one lower-tail estimate: 0.12072</text>', '</svg>']
    return {'width-comparison.svg':'\n'.join(parts)+'\n','selected-null.svg':'\n'.join(s)+'\n','histogram.csv':table.getvalue()}


if __name__ == '__main__':
    for name,text in render().items():(HERE/name).write_text(text,encoding='utf-8',newline='\n')
