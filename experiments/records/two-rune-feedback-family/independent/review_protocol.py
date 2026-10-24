import json,hashlib,itertools,datetime
from pathlib import Path
H=Path(__file__).resolve().parent
D=H.parent/'r12-c1-family-run-2026-10-24'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((D/'protocol-frozen.json').read_bytes())
for r in p['files']:assert sha(D/r['path'])==r['sha256']
for r in json.loads((D/'source-manifest.json').read_bytes())['files']:assert sha(D/r['path'])==r['sha256']
assert len(p['labels'])==56 and len(p['effective_labels'])==48
names=['sum','gemsum','xor','prime_of_sum','prime_of_gemsum','lastdiff','alt_sum']
for li,(f,m,s,direction) in enumerate(itertools.product(names,['pt','mix'],[-1,1],['forward','reverse'])):
 r=p['labels'][li];assert (r['function'],r['history'],r['sign'],r['direction'])==(f,m,s,direction)
 assert r['function_index']==names.index(f) and r['mixed']==int(m=='mix')
 expected=f'{"lastdiff" if f=="alt_sum" else f}-{m}-{(-s if f=="alt_sum" else s):+d}-{direction}'
 assert r['representative']==expected and r['negate_starting_key']==(f=='alt_sum')
assert p['null_seed']==3301241024 and p['null_replicates']==49 and p['absolute_gate']==-5.5 and p['null_margin']==.5
pages=json.loads((D/'pages.json').read_bytes())['pages']
assert len(pages)==55 and sum(len(r['runes']) for r in pages)==12956
assert [r['page'] for r in pages]==[f'lp2-{i:02d}' for i in range(56) if i!=50]
assert len(p['labels'])*55*841==p['labelled_target_cases']==2590280
assert len(p['effective_labels'])*55*841==p['effective_target_cases']==2220240
assert p['prior_overlap']['union_prior_labelled']==56*55*29+55*812==133980
assert p['prior_overlap']['union_prior_effective']==48*55*29+55*812==121220
assert not (D/'observed-effective-scores.npy').exists()
r=dict(reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_sha256=sha(D/'protocol-frozen.json'),all_declared_protocol_and_source_files_verified=True,all56labels_and48representatives_verified=True,all841alias_primer_bijections_verified_in_preflight=True,stable_tie_order='Full alias grid permutation before argmax and stable expanded label/page/primer sort; source function order retained.',matched_nulls='One shared trial RNG shuffles each page once before branch orientation; all labels share49corpora, seeds3301241024..1072.',reuse='No prior score reuse; exact common corner compared after execution.',prior_overlap='133980labelled/121220effective prior settings; additional2456300labelled/2099020effective. Settings are not distinct ideas.',failed_controls_preserved=True,target_outputs_present=False,independent_audit_plan_sha256=sha(H/'audit-plan-frozen.json'),decision='No pre-target blocker for explicitly diagnostic score enumeration. Failed identification controls forbid general family rejection.')
(H/'protocol-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
print('PASS pre-target review',r['protocol_sha256'])
