import hashlib,json,sys
from pathlib import Path
import numpy as np
from numba import njit
HERE=Path(__file__).resolve().parent
@njit
def independently_score(C,vectors,letters,sizes,table):
    out=np.empty((len(vectors),4),np.float64)
    for vi in range(len(vectors)):
        k=vectors[vi,0]
        for seed in range(2):
            for si in range(2):
                sign=-1 if si==0 else 1;chars=0;state=0;total=0.
                for i in range(len(C)):
                    f=0
                    if i>=k:
                        for lag in range(1,k+1):f+=vectors[vi,lag]*C[i-lag]
                    p=(C[i]+sign*((seed+f)%29))%29
                    for pos in range(sizes[p]):
                        state=(state*26+letters[p,pos])%(26**4);chars+=1
                        if chars>3:total+=table[state]
                out[vi,seed*2+si]=total/(chars-3) if chars>3 else -999.
    return out
def main():
    import run
    m=run.source();gp=m.gp;r=json.loads((HERE/'results.json').read_text(encoding='utf-8'));plan=json.loads((HERE/'frozen-plan.json').read_text(encoding='utf-8'));assert hashlib.sha256((HERE/'frozen-plan.json').read_bytes()).hexdigest()==r['plan_sha256']
    for p in plan['inputs']:assert hashlib.sha256((HERE/p['path']).read_bytes()).hexdigest()==p['sha256']
    vectors=[]
    for k in [1,2,3]:
        for coeff in m.coeff_grid(k):vectors.append([k]+coeff[1:]+[0]*(3-k))
    vectors=np.array(vectors,np.int64);labels=gp.TRANSLIT;letters=np.zeros((29,2),np.int64);sizes=np.array(list(map(len,labels)),np.int64)
    assert labels==json.loads((HERE/'labels.json').read_text(encoding='utf-8'))
    for i,label in enumerate(labels):
        for j,ch in enumerate(label):letters[i,j]=ord(ch)-65
    table=np.full(26**4,m.Q.floor)
    for gram,val in m.Q.d.items():table[sum((ord(ch)-65)*26**(3-i) for i,ch in enumerate(gram))]=val
    source_ids=[f'lp2-{i:02d}' for i in list(range(50))+list(range(51,56))];source_pages=dict(zip(source_ids,m.load_pages()[:-2]));pages=json.loads((HERE/'pages.json').read_text(encoding='utf-8'));saved=np.load(HERE/'scores.npz')['scores'];assert saved.size==1054976 and saved.shape==(52,5072,4)
    assert hashlib.sha256(saved.astype('<f8').tobytes()).hexdigest()==r['score_array_sha256']
    worst=0.;best=-999.;bestwhere=None
    for page_index,page in enumerate(pages):
        assert page['runes']==source_pages[page['id']]
        C=np.array(page['runes'],np.int64);scores=independently_score(C,vectors,letters,sizes,table);worst=max(worst,float(np.max(np.abs(scores-saved[page_index]))));assert np.max(np.abs(scores-saved[page_index]))<=2e-12
        if float(scores.max())>best:best=float(scores.max());bestwhere=page_index,int(scores.argmax())
    assert int((saved>=-5.2).sum())==r['above_gate']
    index,flat=bestwhere;vi,arm=divmod(flat,4);w=r['observed'];assert pages[index]['id']==w['page'] and vi==w['coefficient_index'] and arm//2==w['seed'] and (-1 if arm%2==0 else 1)==w['sign'] and abs(best-w['score'])<=2e-12
    # Additional native-source boundary checks span all history depths.
    extra=[]
    C=np.array(r['gate']['controls'][0]['cipher_idx'],np.int64)
    for vi in [0,27,28,867,868,5071]:
        k,a,b,c=map(int,vectors[vi]);native,decoded=m.decode_with_coeffs(C,m.const_seed(0,4000),k,[0,a,b,c][:k+1],-1,0);P=run.decode(C,k,a,b,c,0,-1);value=independently_score(C,vectors[vi:vi+1],letters,sizes,table)[0,0]
        assert decoded['plain_idx']==P.tolist() and abs(native-value)<=2e-12;extra.append({'coefficient_index':vi,'k':k,'delta':abs(native-value)})
    for plant in r['gate']['controls']:
        C=np.array(plant['cipher_idx'],np.int64);s=independently_score(C,vectors,letters,sizes,table);seed=plant['seed'];true=float(s[6,seed*2]);assert true>=float(s.max())-2e-12 and true>-5.2 and float(s[0,seed*2])<-5.5
        native,p=m.decode_with_coeffs(C,m.const_seed(seed,4000),1,[0,7],-1,0);assert p['plain_idx']==plant['truth_idx'] and abs(native-true)<=2e-12
    rng=np.random.default_rng(plan['null_seed'])
    for winner in r['null_maxima']:
        sh={p['id']:rng.permutation(np.array(p['runes'],np.int64)) for p in pages};vi=winner['coefficient_index'];arm=winner['seed']*2+(0 if winner['sign']==-1 else 1);s=independently_score(sh[winner['page']],vectors[vi:vi+1],letters,sizes,table)[0,arm];assert abs(s-winner['score'])<=2e-12
    exceed=sum(v['score']>=w['score'] for v in r['null_maxima']);assert exceed==r['null_exceedances'] and (exceed+1)/33==r['global_empirical_plus_one']
    validation={'all_manuscript_scores':1054976,'max_score_delta':worst,'additional_native_source_checks':extra,'controls':'Both complete20288-setting grids recover exact Warning; true ranks1; native source true-rule paths/scores match.','null_winners_checked':32,'null_full_searches_independently_exhausted':False}
    (HERE/'validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(validation))
if __name__=='__main__':main()
