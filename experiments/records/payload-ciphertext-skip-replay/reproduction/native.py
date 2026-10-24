"""Load only named pinned source definitions; no payload file is opened."""
import ast,importlib.util,random,sys
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;LP=H/'source/liber-primus'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def definitions(path,names,env):
    nodes=[]
    for node in ast.parse(path.read_text(encoding='utf8')).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:nodes.append(node)
        elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in node.targets):nodes.append(node)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),env)

gp=module('payload_scope_gp',LP/'src/lp/gematria.py');sc=module('payload_scope_score',LP/'src/lp/score.py');Q=sc.Quadgram(str(LP/'data/english_quadgrams.txt'))
env=dict(gp=gp,N=29,Q=Q,random=random)
definitions(LP/'analysis/campaign18_skip/skipdecode.py',{'_ALIAS','eng_to_idx','idx_to_trans','encipher_keyskip','_quad_delta','beam_decode'},env)
definitions(LP/'analysis/campaign18_skip/armada/payload_ciphertext.py',{'ANEND_HEX','ANEND_BYTES','_primes','key_phi_prime','key_primes_mod29','key_totient_int','key_thematic','key_anend_hash_mod29','SOLVED_EN','key_solved_lp1','L','THRESHOLD','BEAM_W','candidates'},env)
keys=env['candidates'];decode=env['beam_decode'];encode=env['eng_to_idx'];text=env['idx_to_trans'];encrypt=env['encipher_keyskip']
assert len(keys)==12 and all(len(key)==356 for key in keys.values())

def padded(key,length):
    # Exact source condition and allocation, including its excess appended zeros.
    return key+[0]*(length*4+8) if length*4>=len(key) else list(key)
