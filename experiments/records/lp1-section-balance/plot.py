"""Shared-bin null distributions and the fixed section-slot map; no new test."""
import csv
import hashlib
import io
import json
from math import ceil
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'lp1-word-length-balance'

def render():
    result=json.loads((HERE/'results.json').read_bytes())
    audit=json.loads((HERE/'audit.json').read_bytes())
    assert hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()==audit['report_sha256']
    baseline=json.loads((BASE/'results.json').read_bytes())
    assert result['observed_integer_score']==baseline['observed_integer_score']
    scale=16**3*29**2;bins=40
    maximum=max(max(r['null_integer_scores']) for r in [baseline,result])
    step=ceil((maximum+1)/bins)
    rows=[];histograms=[]
    for label,r in [('Unrestricted',baseline),('Within sections',result)]:
        counts=[0]*bins
        for value in r['null_integer_scores']:counts[value//step]+=1
        assert sum(counts)==r['trials']==49999
        histograms.append(counts)
        rows.extend([label,i*step,(i+1)*step,counts[i]] for i in range(bins))
    maximum_count=max(map(max,histograms))
    head=lambda title,desc,height:[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 {height}" role="img" aria-labelledby="title desc">',f'<title id="title">{title}</title><desc id="desc">{desc}</desc>',f'<rect width="380" height="{height}" fill="white"/>','<style>text{font:14px Arial,sans-serif;fill:#263c47}.title{font-size:18px;font-weight:bold}</style>']
    parts=head('Column balance under two shuffle models','Shared bins and scales. The observed variance is unchanged. Counts at or below it are 54 unrestricted and 88 within sections out of 49999 trials each.',650)
    parts+=['<text x="16" y="29" class="title">Two shuffle models, one arrangement</text>',
        '<text x="16" y="53">Same observed variance · 49,999 shuffles each</text>']
    for panel,(label,r) in enumerate([('Unrestricted',baseline),('Within sections',result)]):
        top=88+panel*250;bottom=top+153
        parts.append(f'<text x="16" y="{top}" class="title">{label}</text>')
        for value in [0,maximum_count//2,maximum_count]:
            y=bottom-value/maximum_count*120
            parts.append(f'<path d="M50 {y:.2f}H354" stroke="#dce2e5"/><text x="43" y="{y+4:.2f}" text-anchor="end" style="font-size:11px">{value}</text>')
        for i,count in enumerate(histograms[panel]):
            h=count/maximum_count*120
            parts.append(f'<rect x="{50+i*7.6:.2f}" y="{bottom-h:.2f}" width="7" height="{h:.2f}" fill="#315e72"/>')
        x=50+r['observed_integer_score']/(step*bins)*304
        parts.append(f'<path d="M{x:.2f} {top+25}V{bottom}" stroke="#a24f2a" stroke-width="2" stroke-dasharray="4 3"/>')
        for frac in [0,.25,.5,.75,1]:
            parts.append(f'<text x="{50+304*frac:.2f}" y="{bottom+20}" text-anchor="middle" style="font-size:12px">{step*bins/scale*frac:.2f}</text>')
        parts.append(f'<text x="16" y="{bottom+46}">At least as flat: {r["lower_tail_with_ties"]} / 49,999</text>')
        parts.append(f'<text x="16" y="{bottom+66}">Plus-one lower-tail estimate: {r["p"]}</text>')
    parts+=['<text x="16" y="602">Column-mean variance (x) · shuffle count (y)</text>',
        '<text x="16" y="623">Dashed line: observed variance, 0.03723</text>',
        '<text x="16" y="644">These are not independent evidence.</text></svg>']
    grid=head('What the within-section shuffle preserves','A 29 by 16 slot map. Section boundaries continue across rows; words may move only among slots of their own section.',565)
    grid+=['<text x="16" y="28" class="title">What stays fixed?</text>',
        '<text x="16" y="51">Shuffle lengths only within their section’s slots.</text>']
    colors=['#d7e7ef','#e7dcc7','#d9e5d5','#e2dced']
    names=['Warning','Welcome','First koan','Second koan'];offset=0
    for i,g in enumerate(result['section_lengths']):
        for position in range(offset,offset+len(g)):
            row,col=divmod(position,16)
            grid.append(f'<rect x="{40+col*19}" y="{83+row*12}" width="18" height="11" fill="{colors[i]}" stroke="#8c969a" stroke-width=".4"/>')
        offset+=len(g)
    for col in [1,4,8,12,16]:grid.append(f'<text x="{40+(col-1)*19+9}" y="76" text-anchor="middle" style="font-size:11px">{col}</text>')
    for row in [1,10,20,29]:grid.append(f'<text x="31" y="{83+(row-1)*12+10}" text-anchor="end" style="font-size:11px">{row}</text>')
    for i,g in enumerate(result['section_lengths']):
        y=452+22*i
        grid+= [f'<rect x="16" y="{y-12}" width="14" height="14" fill="{colors[i]}"/>',f'<text x="39" y="{y}">{names[i]} · {len(g)} words</text>']
    grid+=['<text x="16" y="550">16 columns × 29 rows · sections continue across rows</text></svg>']
    csv_text=io.StringIO(newline='');writer=csv.writer(csv_text,lineterminator='\n')
    writer.writerow(['model','integer_score_bin_start_inclusive','integer_score_bin_end_exclusive','count']);writer.writerows(rows)
    return {'null-comparison.svg':'\n'.join(parts)+'\n','section-slots.svg':'\n'.join(grid)+'\n','histogram.csv':csv_text.getvalue()}

if __name__=='__main__':
    for name,content in render().items():(HERE/name).write_text(content,encoding='utf-8',newline='\n')
