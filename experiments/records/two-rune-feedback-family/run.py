"""Full fixed k2 feedback family; uniform recomputation and compact null receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np
import engine as e

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(value,indent=2)+'\n')


def save_array(name,array):
    with (HERE/name).open('xb') as out:np.save(out,array,allow_pickle=False)


def load_protocol():
    p=json.loads((HERE/'protocol-frozen.json').read_bytes())
    for row in p['files']:
        assert sha(HERE/row['path'])==row['sha256'],row['path']
    for row in json.loads((HERE/'source-manifest.json').read_bytes())['files']:
        assert sha(HERE/row['path'])==row['sha256'],row['path']
    pages=json.loads((HERE/'pages.json').read_bytes())['pages']
    assert len(pages)==55 and sum(len(x['runes']) for x in pages)==12956
    for row in pages:assert hashlib.sha256(bytes(row['runes'])).hexdigest()==row['runes_sha256']
    return p,pages


def witness(page,cipher,label,primer,score,model):
    plain=e.decode(np.asarray(cipher,dtype=np.int64),*primer,label['function_index'],label['mixed'],label['sign'],model[0])
    text=e.source.idx_to_trans(plain)
    tail=e.source.idx_to_trans(plain[2:])
    return {'page':page,'label':label['id'],'function':label['function'],'history':label['history'],
            'sign':label['sign'],'direction':label['direction'],'starting_key':list(map(int,primer)),
            'score':float(score),'runes':plain.tolist(),'decoded_sha256':hashlib.sha256(bytes(plain)).hexdigest(),
            'transliteration':text,'scored_tail':tail,'quadgrams':len(tail)-3}


def shuffled_pages(pages,seed):
    rng=random.Random(seed);out=[]
    for page in pages:
        values=list(page['runes']);rng.shuffle(values);out.append(values)
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    p,pages=load_protocol();assert not (HERE/'results.json').exists(),'Expected results exist; use isolated replay.'
    labels=p['labels'];effective=p['effective_labels'];model=e.setup()
    effective_index={row['id']:i for i,row in enumerate(effective)}
    neg=np.array([(-a)%29*29+(-b)%29 for a in range(29) for b in range(29)])
    checkpoint=HERE/'checkpoints';checkpoint.mkdir(exist_ok=True)
    if not args.resume:assert not list(checkpoint.iterdir()),'Checkpoint exists; explicitly resume or use fresh output.'
    start=time.perf_counter();null_scores=[];null_primers=[];nulls=[]
    for trial in range(50):
        seed=p['null_seed']+trial-1 if trial else None
        ciphers=shuffled_pages(pages,seed) if trial else [list(row['runes']) for row in pages]
        input_hash=hashlib.sha256(b''.join(bytes(x) for x in ciphers)).hexdigest()
        receipt=checkpoint/f'{trial:02}.json'
        if receipt.exists() and args.resume:
            saved=json.loads(receipt.read_bytes());assert saved['protocol_sha256']==sha(HERE/'protocol-frozen.json') and saved['input_sha256']==input_hash
            a=np.load(checkpoint/f'{trial:02}-scores.npy',allow_pickle=False);b=np.load(checkpoint/f'{trial:02}-primers.npy',allow_pickle=False)
            assert sha(checkpoint/f'{trial:02}-scores.npy')==saved['scores_sha256'] and sha(checkpoint/f'{trial:02}-primers.npy')==saved['primers_sha256']
            if trial==0:
                assert sha(HERE/'observed-effective-scores.npy')==saved['observed_effective_scores_sha256']
                assert sha(HERE/'observed-witnesses.json')==saved['observed_witnesses_sha256']
            if trial:null_scores.append(a);null_primers.append(b);nulls.append(saved)
            print('Reused checkpoint',trial,flush=True);continue
        observed=np.empty((48,55,841),dtype='<f8') if trial==0 else None
        best_scores=np.empty((56,55),dtype='<f8');best_primers=np.empty((56,55),dtype='<u2')
        for pi,(page,cipher) in enumerate(zip(pages,ciphers)):
            oriented=[np.asarray(cipher,dtype=np.int64),np.asarray(cipher[::-1],dtype=np.int64)]
            grids=[]
            for ei,label in enumerate(effective):
                values=e.grid(oriented[int(label['direction']=='reverse')],label['function_index'],label['mixed'],label['sign'],*model)
                grids.append(values)
                if trial==0:observed[ei,pi]=values
            for li,label in enumerate(labels):
                values=grids[effective_index[label['representative']]]
                if label['negate_starting_key']:values=values[neg]
                winner=int(np.argmax(values));best_scores[li,pi]=values[winner];best_primers[li,pi]=winner
        flat=int(np.argmax(best_scores));li,pi=divmod(flat,55);label=labels[li];primer=divmod(int(best_primers[li,pi]),29)
        cipher=ciphers[pi][::-1] if label['direction']=='reverse' else ciphers[pi]
        best=witness(pages[pi]['page'],cipher,label,primer,best_scores[li,pi],model)
        saved={'trial':trial,'seed':seed,'protocol_sha256':sha(HERE/'protocol-frozen.json'),'input_sha256':input_hash,'best':best,
               'scores_sha256':None,'primers_sha256':None}
        for suffix,array in [('scores',best_scores),('primers',best_primers)]:
            path=checkpoint/f'{trial:02}-{suffix}.npy'
            with path.open('xb') as out:np.save(out,array,allow_pickle=False)
            saved[suffix+'_sha256']=sha(path)
        if not trial:
            save_array('observed-effective-scores.npy',observed)
            # Expand aliases only in memory to preserve all labelled ties/order.
            expanded=np.empty((56,55,841),dtype='<f8')
            for li,label in enumerate(labels):
                values=observed[effective_index[label['representative']]]
                expanded[li]=values[:,neg] if label['negate_starting_key'] else values
            order=np.argsort(-expanded.reshape(-1),kind='stable')[:40]
            top=[];branches=[]
            for index in order:
                li,rest=divmod(int(index),55*841);pi,primer_index=divmod(rest,841);label=labels[li]
                cipher=ciphers[pi][::-1] if label['direction']=='reverse' else ciphers[pi]
                top.append(witness(pages[pi]['page'],cipher,label,divmod(primer_index,29),expanded[li,pi,primer_index],model))
            for li,label in enumerate(labels):
                pi=int(np.argmax(best_scores[li]));cipher=ciphers[pi][::-1] if label['direction']=='reverse' else ciphers[pi]
                branches.append(witness(pages[pi]['page'],cipher,label,divmod(int(best_primers[li,pi]),29),best_scores[li,pi],model))
            write('observed-witnesses.json',{'best':best,'top40':top,'per_label_best':branches,'effective_score_sha256':sha(HERE/'observed-effective-scores.npy')})
            saved['observed_effective_scores_sha256']=sha(HERE/'observed-effective-scores.npy')
            saved['observed_witnesses_sha256']=sha(HERE/'observed-witnesses.json')
        else:null_scores.append(best_scores);null_primers.append(best_primers);nulls.append(saved)
        with receipt.open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(saved,indent=2)+'\n')
        print(f'Trial {trial}/49 | best {best["score"]:.6f} | {best["label"]} | {best["page"]} | elapsed {time.perf_counter()-start:.1f}s',flush=True)
    a=np.asarray(null_scores,dtype='<f8');b=np.asarray(null_primers,dtype='<u2')
    save_array('null-page-maxima-scores.npy',a);save_array('null-page-maxima-primers.npy',b)
    observed=json.loads((HERE/'observed-witnesses.json').read_bytes());maximum=float(np.max(a));bar=max(-5.5,maximum+.5)
    # Score counts per label and effective branch; do not count aliases as ideas.
    scores=np.load(HERE/'observed-effective-scores.npy',allow_pickle=False)
    hits=[]
    for li,label in enumerate(labels):
        values=scores[effective_index[label['representative']]]
        if label['negate_starting_key']:values=values[:,neg]
        for pi,primer_index in np.argwhere(values>=bar):
            cipher=pages[int(pi)]['runes'];cipher=cipher[::-1] if label['direction']=='reverse' else cipher
            hits.append(witness(pages[int(pi)]['page'],cipher,label,divmod(int(primer_index),29),values[pi,primer_index],model))
    write('results.json',{'protocol_sha256':sha(HERE/'protocol-frozen.json'),'observed':observed,'null_global_witnesses':nulls,
                         'null_maximum':maximum,'hit_bar':bar,'gate_hits':hits,'null_ge_observed':int(np.sum(np.max(a,axis=(1,2))>=observed['best']['score'])),
                         'labelled_cases':2590280,'effective_cases':2220240,'null_replicates':49,
                         'observed_effective_scores_sha256':sha(HERE/'observed-effective-scores.npy'),
                         'null_page_scores_sha256':sha(HERE/'null-page-maxima-scores.npy'),'null_page_primers_sha256':sha(HERE/'null-page-maxima-primers.npy'),
                         'seconds':time.perf_counter()-start,'reused_prior_scores':False,
                         'interpretation':'Fixed score-screening enumeration after failed unique-identification controls; no validated cipher-family rejection.'})
    print('Complete; hits',len(hits),'whole-family shuffled maxima >=observed',int(np.sum(np.max(a,axis=(1,2))>=observed['best']['score'])),'/49',flush=True)


if __name__=='__main__':main()
