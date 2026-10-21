"""Render the six cyclic classes and complete selected-null histogram."""
import csv
import io
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def frame(height,title,description):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{title}</title><desc id="desc">{description}</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#25343a;font-size:13px}.small{font-size:11px}</style>']

def render():
    data=json.loads((HERE/'results.json').read_bytes())
    s=frame(650,'24 orders, six cyclic classes','Every group contains four cyclic rotations with identical balance score. Lower Q means more similar column totals.')
    s += ['<text x="18" y="28" font-size="18">24 orders, six balance scores</text>',
        '<text x="18" y="52">A: Warning · B: Welcome</text>',
        '<text x="18" y="73">C: First koan · D: Second koan</text>',
        '<text x="18" y="96">Lower Q means more balanced columns.</text>']
    for c,(rep,q) in enumerate(zip(data['class_representatives'],data['observed_class_scores'])):
        y=127+c*78
        orders=[o for o,k in zip(data['orders'],data['order_class_indices']) if k==c]
        label='   '.join(''.join('ABCD'[i] for i in order) for order in orders)
        s += [f'<text x="18" y="{y}">{label}</text>',
            f'<rect x="18" y="{y+10}" width="{260*q/max(data["observed_class_scores"]):.2f}" height="14" fill="#42687b"/>',
            f'<text x="18" y="{y+43}" class="small">Q = {q:,}</text>']
    s += ['<text x="18" y="607">Original ABCD order ties with its rotations.</text>',
        '<text x="18" y="628">Classes are not independent tests.</text>','</svg>']
    values=[t['minimum'] for t in data['trials']]
    bins=32;step=(max(values)//bins+1);counts=[0]*bins
    for v in values:counts[min(v//step,bins-1)]+=1
    assert sum(counts)==49999
    csvfile=io.StringIO(newline='');writer=csv.writer(csvfile,lineterminator='\n')
    writer.writerow(['lower_Q_inclusive','upper_Q_exclusive','trials'])
    for i,n in enumerate(counts):writer.writerow([i*step,(i+1)*step,n])
    h=frame(390,'Minimum balance score after searching all orders','Histogram of all 49,999 within-section shuffle trials. Each trial searches all 24 orders. Dashed line shows observed minimum 128256. 440 controls are no greater.')
    h += ['<text x="18" y="27">Give every control the same order search</text>',
        '<text x="18" y="50" class="small">49,999 controls · 32 equal-width bins · all trials shown</text>']
    left=48;top=80;width=308;height=205;peak=max(counts)
    for frac in [0,.5,1]:
        y=top+height*(1-frac)
        h += [f'<path d="M48 {y} H356" stroke="#d9dfe1"/>',f'<text x="43" y="{y+4}" text-anchor="end" class="small">{peak*frac:g}</text>']
    for i,n in enumerate(counts):
        bh=height*n/peak
        h.append(f'<rect x="{left+i*width/bins:.2f}" y="{top+height-bh:.2f}" width="{width/bins-.5:.2f}" height="{bh:.2f}" fill="#42687b"/>')
    x=left+width*data['observed_minimum']/(bins*step)
    h += [f'<path d="M{x:.2f} {top} V{top+height}" stroke="#9b3c2e" stroke-width="2" stroke-dasharray="5 3"/>',
        f'<text x="{x+4:.2f}" y="72" class="small">Observed: 128,256</text>',
        '<text x="48" y="303" class="small">0</text>',
        f'<text x="356" y="303" text-anchor="end" class="small">{bins*step:,}</text>',
        '<text x="202" y="325" text-anchor="middle">Minimum Q across all 24 orders</text>',
        '<text x="18" y="351">440 controls at or below the observed score.</text>',
        '<text x="18" y="373">Plus-one estimate: 441 / 50,000 = 0.00882</text>','</svg>']
    return {'order-classes.svg':'\n'.join(s)+'\n','selected-null.svg':'\n'.join(h)+'\n','histogram.csv':csvfile.getvalue()}

if __name__=='__main__':
    for name,content in render().items():
        (HERE/name).write_text(content,encoding='utf-8',newline='\n')
