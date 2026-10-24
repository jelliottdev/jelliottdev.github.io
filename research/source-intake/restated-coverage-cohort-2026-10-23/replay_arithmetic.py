import ast,collections,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SRC=ROOT.parent/'source-cache/dukotah-cicada3301';LP=SRC/'liber-primus'
tree=ast.parse((LP/'benchmark/null.py').read_text()); names={'DEFAULT_MU','DEFAULT_BETA','FIXED_BAR'}
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name=='threshold_for') or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets))]
ns={'math':math};exec(compile(ast.Module(body=nodes,type_ignores=[]),'source-threshold-subset','exec'),ns)
cross=math.exp((ns['FIXED_BAR']-ns['DEFAULT_MU'])/ns['DEFAULT_BETA'])*(-math.log(.99))
rows=[]
for N in [40,768,1000,52556,71000,692064,6224300,math.floor(cross),math.ceil(cross),2520000000]:
    actual=ns['threshold_for'](N);independent=max(-5.5,-7.2517+.0725*math.log(N/(-math.log1p(-.01))))
    assert abs(actual-independent)<1e-12
    rows.append({'N':N,'bar':actual,'fixed_floor_binds':actual==-5.5})
assert rows[-1]['bar']>-5.5
b=json.loads((LP/'analysis/round22/B-turtle-spatial-render/ledger.json').read_text())
counts=collections.Counter();mismatch=0
for row in b['rows']:
    hits={stat for stat,p in row['null_p'].items() if p<.01};counts.update(hits)
    mismatch+=hits!=set(row['hits_at_0.01'])
assert len(b['rows'])==72 and mismatch==0 and sum(counts.values())==6
poisson=1-sum(math.exp(-2.88)*2.88**k/math.factorial(k) for k in range(6))
binomial=1-sum(math.comb(288,k)*.01**k*.99**(288-k) for k in range(6))
s=json.loads((LP/'analysis/round21/L1-seal-realmode-proxy/catch_surface.json').read_text())
for row in s['catch_surface']:
    assert row['catch_rate']==row['catch']/row['catch_n']
    assert row['genuine_false_reject_rate']==row['genuine_false_reject']/row['genuine_n']
eligible=[r for r in s['catch_surface'] if r['genuine_false_reject_rate']<=.1]
winner=sorted(eligible,key=lambda r:(-r['catch_rate'],r['k_folds'],['min','mean','frac_pass'].index(r['agree_rule'])))[0]
assert winner==s['tuning_winner'] and winner['k_folds']==5 and winner['agree_rule']=='min'
out={'threshold_source_subset':'benchmark/null.py::threshold_for and its literal constants, AST-extracted unchanged','crossover_N':cross,'bars':rows,'round22_saved_row_recount':{'rows':72,'nominal_p_below_001':dict(counts),'total':sum(counts.values()),'hit_list_mismatches':mismatch,'flagged_for_oracle':b['flagged_for_oracle'],'poisson_tail_for_6':poisson,'binomial_tail_for_6':binomial,'limitation':'Counts recomputed from saved p-values; no geometry/null campaign rerun. Distribution tails assume the stated Poisson/binomial model; do not establish test independence.'},'round21_saved_surface':{'rows':len(s['catch_surface']),'winner':winner,'heldout_surrogate':s['heldout_surrogate_audit'],'limitation':'Saved arithmetic and winner rule only; no source-panel catch reconstruction.'}}
(HERE/'arithmetic.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS: threshold subset, saved geometry counts and saved fold-surface arithmetic')
