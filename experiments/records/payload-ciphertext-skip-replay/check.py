"""Validate saved evidence and source scores using only bundled standard-library inputs."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'reproduction'))
import native as n
def main():
    record=json.loads((H/'record.json').read_bytes());prefix='experiments/records/payload-ciphertext-skip-replay/'
    for role in ('inputs','outputs'):
        for item in record['reproduction'][role]:
            assert item['path'].startswith(prefix)
            assert hashlib.sha256((H/item['path'][len(prefix):]).read_bytes()).hexdigest()==item['sha256'],item['path']
    r=H/'reproduction'
    for name in ('controls-plan-frozen.json','controls-execution-frozen.json','target-protocol-frozen.json'):
        plan=json.loads((r/name).read_bytes())
        for path,digest in plan['pins'].items():assert hashlib.sha256((r/path).read_bytes()).hexdigest()==digest,path
    for item in plan['targets']:assert hashlib.sha256((r/item['path']).read_bytes()).hexdigest()==item['sha256']
    d=json.loads((r/'target-results.json').read_bytes());rows=d['cases'];assert len(rows)==d['attempts']==d['completed']==96 and d['errors']==0
    for row in rows:
        source=row['source'];terminal=row['terminal'];assert len(source['plain_idx'])==len(terminal['best_normalized_output'])==256
        assert source['translit']==n.text(source['plain_idx']) and n.Q.score_norm(source['translit'])==source['score']
        assert n.Q.score_norm(n.text(terminal['best_normalized_output']))==terminal['best_normalized_score']
        scores=row['terminal_normalized_scores'];assert len(scores)==terminal['terminal_count'] and scores[0]==source['score']
        assert max(scores)==terminal['best_normalized_score'] and scores.index(max(scores))+1==terminal['best_normalized_rank']
        assert row['source_gate']==(source['score']> -5.5) and row['normalized_gate']==(max(scores)> -5.5)
    assert sum(x['source_gate'] for x in rows)==d['source_gate_passes']==0 and sum(x['normalized_gate'] for x in rows)==d['normalized_gate_passes']==0
    assert sum(x['terminal']['terminal_count'] for x in rows)==d['retained_terminals']==27062
    c=json.loads((r/'controls-results.json').read_bytes());assert c['summary']['attempts']==144 and c['summary']['exact_recoveries']==137 and c['summary']['source_gate_passes']==144 and c['summary']['wrong_key_gate_passes']==0
    assert c['summary']['boundary_cases']==24 and c['summary']['allocation_checks']==96
    print('PASS: declared bytes,96 source/normalized winners,all terminal score selections and frozen control counts')
if __name__=='__main__':main()
