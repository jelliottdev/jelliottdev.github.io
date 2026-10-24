"""Reproduce exploratory scientific outputs and check preserved original bytes."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
before={n:(HERE/n).read_bytes() for n in ['plan-frozen-original.json','plan.json','results.json','cases.json']}
saved=json.loads((HERE/'calibration-results.json').read_bytes());saved.pop('elapsed_seconds_informational',None)
subprocess.run(['python',str(HERE/'calibrate.py')],check=True)
assert json.loads((HERE/'calibration-results.json').read_bytes())==saved
assert all((HERE/n).read_bytes()==v for n,v in before.items())
r=saved;assert len(r['null_trials'])==128 and all(len(t['per_keyword_hits'])==45 and max(t['per_keyword_hits'])==t['global_key_maximum'] for t in r['null_trials'])
assert r['null_global_maxima']==[t['global_key_maximum'] for t in r['null_trials']]
assert r['maxima_at_least_observed']==sum(x>=126 for x in r['null_global_maxima'])
p=r['known_warning_control'];assert p['score_rank_controls']==45 and p['true_top_ranked']==45 and p['exact_recovered']==45
assert p['runes']==sum(p['word_lengths'])==184 and p['word_slots']==45
for row in p['ranked_rows']:
 assert row['true_plaintext_hits']==30 and row['true_rank_competition']==1 and max(row['all_key_scores'])==30
print('Post-target calibration reproduces;128 complete max searches and45 score/rank controls checked. Original plans/results/cases unchanged.')
