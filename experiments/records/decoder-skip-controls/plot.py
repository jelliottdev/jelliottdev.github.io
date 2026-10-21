"""Generate complete control counts and charts from the independently checked report."""
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
report=json.loads((HERE/'results.json').read_bytes())
audit=json.loads((HERE/'audit.json').read_bytes())
assert audit['report_sha256']==hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()
assert audit['decoder_results_checked']==2160
groups={}
for plant in report['plants']:
    for r in plant['results']:
        key=(plant['encoder'],plant['key_repetition'],r['key_condition'],r['decoder'],r['width'],r['maximum_skip'])
        row=groups.setdefault(key,dict(zip(['encoder','key_repetition','key_condition','decoder','beam_width','maximum_skip'],key),
                                      samples=0,exact_recovery=0,score_accepted=0,truth_path_invalid=0,truth_prefix_pruned=0))
        row['samples']+=1;row['exact_recovery']+=r['exact_match'];row['score_accepted']+=r['score_accepted']
        row['truth_path_invalid']+=r['first_invalid_truth_step'] is not None
        row['truth_prefix_pruned']+=r['first_pruned_truth_step'] is not None
assert len(groups)==80 and all(r['samples']==27 for r in groups.values())
with (HERE/'summary.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(next(iter(groups.values()))));writer.writeheader();writer.writerows(groups.values())
names={'rigid':'Ordinary addition','skip':'Key skipping','rewrite':'Value rewriting','drift-skip':'Unrelated advance + skipping'}
configs=[('rigid',None,0)]+[('beam',w,s) for w in (16,64) for s in (1,3)]
for repeat in (1,4):
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 1080" role="img" aria-labelledby="t d">',
         '<title id="t">Exact recovery and score acceptance with the correct key</title>',
         '<desc id="d">All four encoder variants and five decoder settings. Blue bars count exact recovery, outlined bars count score acceptance, each out of 27 plants. A passing score need not mean correct runes.</desc>',
         '<rect width="380" height="1080" fill="white"/><style>text{font:12px Arial,sans-serif;fill:#273c47}</style>',
         f'<text x="12" y="23" style="font-size:16px;font-weight:bold">Correct key · {"single values" if repeat==1 else "four-slot runs"}</text>',
         '<rect x="12" y="39" width="16" height="8" fill="#315f76"/><text x="34" y="47">Exact rune recovery</text>',
         '<rect x="12" y="58" width="16" height="8" fill="white" stroke="#987650"/><text x="34" y="66">Score ≥ −5.5</text>',
         '<text x="12" y="87">Counts out of 27 · beam labels: width / skip limit</text>']
    for panel,encoder in enumerate(names):
        top=115+panel*235
        svg.append(f'<text x="12" y="{top}" style="font-weight:bold">{names[encoder]}</text>')
        for i,(decoder,width,limit) in enumerate(configs):
            r=groups[(encoder,repeat,'correct',decoder,width,limit)];y=top+25+i*36
            label='Rigid' if decoder=='rigid' else f'Beam {width} / {limit}'
            svg.append(f'<text x="12" y="{y+10}">{label}</text>')
            for offset,field,style in [(0,'exact_recovery','fill="#315f76"'),(11,'score_accepted','fill="white" stroke="#987650"')]:
                count=r[field];length=190*count/27
                svg.append(f'<rect x="132" y="{y+offset}" width="{length}" height="8" {style}/><text x="340" y="{y+offset+8}">{count}</text>')
        svg.append(f'<path d="M132 {top+210}H322" stroke="#cbd2d5"/><text x="132" y="{top+225}">0</text><text x="322" y="{top+225}" text-anchor="end">27</text>')
    svg+=['<text x="12" y="1070">Wrong keys: no exact recovery or accepted scores.</text>','</svg>']
    (HERE/f'key-runs-{repeat}.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')
print('Rendered all 40 correct-key cells; CSV retains all 80 correct/wrong-key cells')
