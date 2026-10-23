"""Partial source replay of Round 12 D1: the two recovered Mabinogion rows only."""

import ast
import hashlib
import json
import pathlib
import runpy

WORK = pathlib.Path(__file__).resolve().parents[3]
SRC = WORK / 'source-cache/dukotah-cicada3301/liber-primus/analysis/round12/D1_redteam/rewrite_gate.py'
KEY = WORK / 'source-cache/corpus-input-probes-20261023/mabinogion-current.txt'
ARCHIVE = SRC.with_name('rewrite_gate_results.json')
ns = runpy.run_path(str(SRC))
tree = ast.parse(SRC.read_text(encoding='utf-8'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
plain = next(n.value for n in fn.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'plain' for t in n.targets))
P = ns['eng_to_idx'](ast.literal_eval(plain))
K = ns['eng_to_idx'](KEY.read_text(encoding='utf-8'))
archived = json.loads(ARCHIVE.read_text(encoding='utf-8'))
rows = []
for i, offset in enumerate((137, 4096)):
    skip_c, skips, _ = ns['encipher_keyskip'](P, K[offset:], sign=-1, supp=.83, seed=offset+7)
    skip = ns['beam_decode'](skip_c, K, sign=-1, o=offset, beam_w=600, max_skip=3)
    rewrite_c, n_rewrite = ns['encipher_rewrite'](P, K[offset:], sign=-1, supp=.83, seed=offset+7)
    rewrite = ns['beam_decode'](rewrite_c, K, sign=-1, o=offset, beam_w=600, max_skip=3)
    rigid = ns['rigid_decode'](rewrite_c, K, sign=-1, o=offset)
    assert skip['score'] == archived['skip_scores'][i]
    assert rewrite['score'] == archived['rewrite_beam'][i]
    assert rigid['score'] == archived['rewrite_rigid'][i]
    rows.append({'offset': offset, 'skip_count': sum(skips), 'rewrite_count': n_rewrite,
                 'skip_score': skip['score'], 'rewrite_beam_score': rewrite['score'],
                 'rewrite_rigid_score': rigid['score'],
                 'skip_plain_match': sum(a == b for a,b in zip(skip['plain_idx'],P))/len(P),
                 'rewrite_plain_match': sum(a == b for a,b in zip(rewrite['plain_idx'],P))/len(P)})
print(json.dumps({'key_sha256': hashlib.sha256(KEY.read_bytes()).hexdigest(),
                  'key_bytes': KEY.stat().st_size, 'key_runes': len(K),
                  'plaintext_runes': len(P), 'rows': rows}, indent=2))
