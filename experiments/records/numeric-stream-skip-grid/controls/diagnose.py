"""Explain all full-reading control mismatches; no manuscript inputs decoded."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
import probe
HERE=Path(__file__).resolve().parent
def main():
    a,b,enc,s,streams=probe.load();keys={(br,n):k for br,n,k in streams}
    readings=json.loads((HERE/'known-readings.json').read_text());data=json.loads((HERE/'control-results.json').read_text());out=[]
    for r in data['rows']:
        if not r['eligible'] or r['full_exact']:continue
        P=readings[r['reading']];K=keys[r['branch'],r['name']];C,sk,used=enc.encipher_keyskip(P,K[r['offset']:],sign=r['sign'],supp=.83,seed=r['seed'])
        true_valid=True
        for i in range(1,len(P)):
            for m in range(used[i-1]+1,used[i]):
                if (P[i]-r['sign']*K[r['offset']+m])%29!=C[i-1]:true_valid=False
        assert sk==r['skips'] and max(sk)<=3 and true_valid
        pred=s.beam(np.array(C),np.array(K),r['sign'],r['offset'],len(P),200 if r['branch']=='numeric' else 300)
        assert hashlib.sha256(bytes(pred)).hexdigest()==r['decoded_sha256']
        truth=s.Q.score(enc.idx_to_trans(P));chosen=s.Q.score(enc.idx_to_trans(pred));delta=chosen-truth
        classification='tie' if abs(delta)<1e-10 else ('strictly_higher_alternative' if delta>0 else 'lower_scoring_alternative_true_path_pruned')
        out.append({k:r[k] for k in ['branch','name','sign','atbash','offset','reading','seed','skip_total','skip_max']}|{'true_path_valid':true_valid,'genuine_skips':sum(sk)>0,'classification':classification,'truth_cumulative_score':truth,'chosen_cumulative_score':chosen,'cumulative_delta':delta,'truth_normalized_score':s.Q.score_norm(enc.idx_to_trans(P)),'chosen_normalized_score':r['full_score'],'rune_differences':sum(x!=y for x,y in zip(P,pred)),'changed_positions':[i for i,(x,y) in enumerate(zip(P,pred)) if x!=y]})
    probe.write(HERE/'failure-diagnosis.json',{'classification_rule':'Compare cumulative raw quadgram scores actually used by source beam; tie tolerance1e-10. True-path validity checked against each suppressed-doublet constraint. All previously observed mismatches retained.','rows':out})
    from collections import Counter
    print('Failures',len(out),'classification',Counter(r['classification'] for r in out),'genuine',sum(r['genuine_skips'] for r in out),'valid',sum(r['true_path_valid'] for r in out))
if __name__=='__main__':main()
