"""Post-target audit of normalized scores of retained terminal hypotheses."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

import run

HERE = Path(__file__).resolve().parent


def main():
    plan = json.loads((HERE/'terminal-plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert run.sha(run.ROOT/item['path']) == item['sha256'], item['path']
    source, sweep, _, streams, pages = run.load()
    keys = {x['name']:x['key'] for x in streams}
    page_map = dict(zip(run.PLAN['page_ids'],pages))
    node = next(n for n in ast.parse(Path(sweep.__file__).read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef) and n.name=='beam')
    code = ast.unparse(node)
    assert 'return list(best[3])' in code
    code = code.replace('return list(best[3])','return beams')
    env = dict(sweep.__dict__)
    exec(compile(code,'<terminal-beam-observer>','exec'),env)
    rows = json.loads((HERE/'cases.json').read_text(encoding='utf8'))
    audit = []
    for r in rows:
        if not r['selected_full']:
            continue
        cipher = np.array(page_map[r['page']],dtype=np.int64)
        if r['atbash']:
            cipher=28-cipher
        terminal = env['beam'](cipher,np.array(keys[r['stream']],dtype=np.int64),r['sign'],r['offset'],len(cipher),300)
        selected = max(terminal,key=lambda x:x[0])
        assert hashlib.sha256(bytes(selected[3])).hexdigest() == r['full_sha256']
        assert abs(source.Q.score_norm(selected[2])-r['full_score'])<1e-12
        normalized = [source.Q.score_norm(x[2]) for x in terminal]
        rank = max(range(len(terminal)),key=lambda i:normalized[i])
        best=terminal[rank]
        audit.append({k:r[k] for k in ['stream','page','sign','atbash','offset']} | {
            'terminal_hypotheses':len(terminal),'source_selected_score':r['full_score'],
            'best_normalized_terminal_score':normalized[rank],
            'best_normalized_cumulative_rank_zero_based':rank,
            'strictly_better_normalized':normalized[rank]>r['full_score']+1e-12,
            'source_gate_pass':r['full_score']> -5.5,'terminal_gate_pass':normalized[rank]> -5.5,
            'best_terminal_indices':list(best[3]),
            'best_terminal_sha256':hashlib.sha256(bytes(best[3])).hexdigest()})
    report = {'schema':'artifact-stream-terminal-audit-v1','terminal_plan_sha256':run.sha(HERE/'terminal-plan.json'),
              'timing':'Separate post-target retained-beam diagnostic; historical source outputs unchanged.',
              'source_full_settings':len(audit),'terminal_hypotheses_scored':sum(r['terminal_hypotheses'] for r in audit),
              'settings_with_better_normalized_terminal':sum(r['strictly_better_normalized'] for r in audit),
              'source_gate_passes':sum(r['source_gate_pass'] for r in audit),
              'terminal_gate_passes':sum(r['terminal_gate_pass'] for r in audit),
              'new_gate_crossings':sum(r['terminal_gate_pass'] and not r['source_gate_pass'] for r in audit),
              'best_normalized_terminal':max(audit,key=lambda r:r['best_normalized_terminal_score']),
              'rows':audit,'limit':'Only retained terminal hypotheses from the 194 source-selected full decodes; no normalized-score reranking at intermediate steps or rejected-screen full decodes.'}
    (HERE/'terminal-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['rows','best_normalized_terminal']},indent=2))


if __name__=='__main__':
    main()
