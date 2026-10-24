"""Explain already-frozen nonexact control outputs without changing any case."""
import hashlib,json
from pathlib import Path
import native as n
from controls import observe
H=Path(__file__).resolve().parent
if __name__=='__main__':
    d=json.loads((H/'controls-results.json').read_bytes());f={x['id']:x['indices'] for x in json.loads((H/'control-fixtures-frozen.json').read_bytes())['fixtures']};rows=[]
    for x in d['positive_cases']:
        if x.get('exact_recovery',True):continue
        ct=[28-v for v in x['ciphertext']] if x['atbash'] else x['ciphertext'];beams,_=observe(ct,n.keys[x['key']],sign=x['sign'],o=0,beam_w=300,max_skip=3)
        truth=next(b for b in beams if b[3]==f[x['fixture']]);winner=beams[0];assert winner[3]==x['source']['plain_idx']
        rows.append(dict(case=x['case'],fixture=x['fixture'],key=x['key'],sign=x['sign'],atbash=x['atbash'],truth_first_rank=x['terminal']['truth_first_rank'],winner_cumulative=winner[0],truth_cumulative=truth[0],strictly_higher_cumulative=winner[0]>truth[0],cumulative_tie=winner[0]==truth[0],winner_normalized=n.Q.score_norm(winner[2]),truth_normalized=n.Q.score_norm(truth[2]),wrong_winner_worse_normalized=n.Q.score_norm(winner[2])<n.Q.score_norm(truth[2])))
    out=dict(stage='Post-control diagnosis only; no target bytes read',controls_sha256=hashlib.sha256((H/'controls-results.json').read_bytes()).hexdigest(),nonexact_cases=rows,strict_cumulative_losses=sum(x['strictly_higher_cumulative'] for x in rows),ties=sum(x['cumulative_tie'] for x in rows),wrong_winners_worse_normalized=sum(x['wrong_winner_worse_normalized'] for x in rows))
    p=H/'failure-analysis.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print(out)
