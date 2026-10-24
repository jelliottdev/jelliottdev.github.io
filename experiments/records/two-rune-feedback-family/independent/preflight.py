"""Pre-target independent checker validation against frozen synthetic/source evidence."""
import sys,json,random,time,hashlib,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import independent as I
H=Path(__file__).resolve().parent;P=H.parent/'r12-c1-family-engine-2026-10-24'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sys.path.insert(0,str(P/'source/analysis/round12/C1'));import feedback as source
    model=I.setup(P/'source');base,primes,letters,table=model
    rng=random.Random(2410263302);C=np.array([rng.randrange(29) for _ in range(61)],dtype=np.int64)
    checked=0;maxerror=0.;started=time.perf_counter()
    for fi,name in enumerate(I.NAMES):
        for mixed in (0,1):
            for sign in (-1,1):
                for reverse in (False,True):
                    ct=C[::-1].copy() if reverse else C
                    values=I.grid(ct,fi,mixed,sign,*model)
                    for index in range(841):
                        a,b=divmod(index,29);got=I.decode(ct,a,b,fi,mixed,sign,base,primes).tolist()
                        expected=source.decode(ct.tolist(),source.F_BASIS[name],2,[a,b],source='mix' if mixed else 'pt',sign=sign)
                        assert got==expected
                        error=abs(values[index]-source.score_norm(expected[2:]));assert error<1e-12;maxerror=max(maxerror,error);checked+=1
    # Exhaustive signed function tables and the exact full seed permutation.
    aliases=[]
    for sign in (-1,1):
        for x in range(29):
            for y in range(29):assert sign*I.key_value(x,y,5,base,primes)%29==(-sign)*I.key_value(x,y,6,base,primes)%29
        permutation=[((-a)%29)*29+(-b)%29 for a in range(29) for b in range(29)]
        assert len(set(permutation))==841 and all(permutation[permutation[i]]==i for i in range(841))
        aliases.append(dict(lastdiff_sign=sign,alt_sum_sign=-sign,primer_permutation=permutation))
    controls=json.loads((P/'control-witnesses.json').read_bytes());wchecked=0
    for row in controls['witnesses']:
        plain=controls['true_passages'][row['text']];fi=I.NAMES.index(row['function']);mixed=int(row['source']=='mix');sign=row['sign'];cipher=[]
        for i,p in enumerate(plain):
            if i<2:k=row['true_primer'][i]
            else:
                x,y=plain[i-2:i]
                if mixed:x=(x+cipher[i-2])%29;y=(y+cipher[i-1])%29
                k=I.key_value(x,y,fi,base,primes)
            cipher.append((p-sign*k)%29)
        actual=I.decode(np.array(cipher),*row['selected_primer'],fi,mixed,sign,base,primes)
        assert actual.tolist()==row['selected_full_indices']
        assert abs(I.score(actual,letters,table)-row['selected_score'])<1e-12
        assert [i for i,(a,b) in enumerate(zip(plain,actual)) if a!=b]==row['mismatch_positions_zero'];wchecked+=1
    r=dict(independent_script_sha256=sha(H/'independent.py'),preflight_script_sha256=sha(H/'preflight.py'),source_manifest_sha256=sha(P/'source-manifest.json'),prototype_plan_sha256=sha(P/'proposal-frozen.json'),synthetic_arrays_and_scores_checked=checked,maximum_score_error=maxerror,failed_control_witnesses_checked=wchecked,alias_signed_table_pairs_checked=1682,alias_map=aliases,target_data_loaded=False,seconds=time.perf_counter()-started,method='Independent direct function formulas and separately allocated decoded/expanded-letter arrays; raw quadgram counts; full original source synthetic comparison. No production engine function table/grid reused.')
    (H/'preflight-receipt.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print(checked,'arrays/scores;',wchecked,'failed witnesses; maximum error',maxerror,'seconds',r['seconds'])
if __name__=='__main__':main()
