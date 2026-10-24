"""Independent direct recurrence and string-quadgram reconstruction."""
import hashlib
import json
import math
import random
import time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
TRANS=('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')


def decode(cipher,primer):
    plain=[]
    for i,c in enumerate(cipher):
        key=primer[i] if i<2 else plain[-1]+plain[-2]
        plain.append((c-key)%29)
    return plain


def main():
    start=time.perf_counter()
    plan=json.loads((HERE/'plan-frozen.json').read_bytes())
    result=json.loads((HERE/'results.json').read_bytes())
    assert result['plan_sha256']==hashlib.sha256((HERE/'plan-frozen.json').read_bytes()).hexdigest()
    assert result['scores_sha256']==hashlib.sha256((HERE/'scores.npy').read_bytes()).hexdigest()
    counts={}
    for line in (HERE/'source/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,count=line.split();counts[gram]=int(count)
    logtotal=math.log10(sum(counts.values()))
    table={gram:math.log10(count)-logtotal for gram,count in counts.items()}
    floor=math.log10(.01)-logtotal
    def score(plain):
        text=''.join(TRANS[r] for r in plain[2:])
        if len(text)<4:return -999.0
        total=0.0
        for i in range(len(text)-3):total+=table.get(text[i:i+4],floor)
        return total/(len(text)-3)
    pages=json.loads((HERE/'pages.json').read_bytes())['pages']
    scores=np.load(HERE/'scores.npy',allow_pickle=False)
    assert scores.shape==(50,55,841) and np.isfinite(scores).all()
    digest=hashlib.sha256();maximum_error=0.0;cases=0
    for pi,row in enumerate(pages):
        for a in range(29):
            for b in range(29):
                plain=decode(row['runes'],[a,b]);digest.update(bytes(plain))
                maximum_error=max(maximum_error,abs(score(plain)-float(scores[0,pi,a*29+b])))
                cases+=1
    assert maximum_error<=1e-12
    assert digest.hexdigest()==result['observed']['all_decodes_sha256']
    bypage={row['page']:row for row in pages}
    def witness(row,cipher):
        plain=decode(cipher,row['primer'])
        assert plain==row['runes'] and hashlib.sha256(bytes(plain)).hexdigest()==row['decoded_sha256']
        assert abs(score(plain)-row['score'])<=1e-12
        text=''.join(TRANS[r] for r in plain[2:])
        assert text==row['scored_transliteration'] and len(text)-3==row['quadgrams']
    for row in result['observed']['top']+result['gate_hits']:
        witness(row,bypage[row['page']]['runes'])
    expected_order=np.argsort(-scores[0].reshape(-1),kind='stable')[:plan['top_witnesses']]
    for row,flat in zip(result['observed']['top'],expected_order):
        pi,index=divmod(int(flat),841)
        assert row['page']==pages[pi]['page'] and row['primer']==list(divmod(index,29))
    for i,row in enumerate(result['nulls']):
        assert row['seed']==plan['null_seed']+i
        rng=random.Random(row['seed']);cipher=None
        for page in pages:
            shuffled=list(page['runes']);rng.shuffle(shuffled)
            if page['page']==row['best']['page']:cipher=shuffled
        witness(row['best'],cipher)
        flat=int(np.argmax(scores[i+1]));pi,index=divmod(flat,841)
        assert row['best']['page']==pages[pi]['page'] and row['best']['primer']==list(divmod(index,29))
        assert row['best']['score']==float(np.max(scores[i+1]))
    largest=max(row['best']['score'] for row in result['nulls'])
    assert result['largest_null']==largest and result['hit_bar']==max(plan['absolute_gate'],largest+plan['null_margin'])
    assert len(result['gate_hits'])==int(np.sum(scores[0]>=result['hit_bar']))
    assert result['null_ge_observed']==sum(np.max(scores[i+1])>=np.max(scores[0]) for i in range(49))
    assert result['prior_diagonal_cases']==1595 and result['new_off_diagonal_cases']==44660 and cases==46255
    assert result['observed']['diagonal_best']==float(np.max(scores[0,:,np.arange(29)*30]))
    assert result['observed']['off_diagonal_best']==float(np.max(scores[0,:,[a*29+b for a in range(29) for b in range(29) if a!=b]]))
    receipt={'status':'PASS','all_target_decodes':cases,'all_target_scores_max_error':maximum_error,
             'decoded_stream_hash':digest.hexdigest(),'top_witnesses':len(result['observed']['top']),
             'null_maximum_witnesses':49,'all_saved_arrays_shape':list(scores.shape),
             'checks':'Direct recurrence, independent string-quadgram scorer, all target decoded bytes and scores, retained top outputs and49 null maximum witnesses, saved full-grid maximum selection and decision arithmetic.',
             'limits':'Does not independently rescore every nonwinning shuffled candidate. Native parity and independent all-target scoring validate the producer; null maxima are separately reconstructed.',
             'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'results_sha256':hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest(),
             'seconds':time.perf_counter()-start}
    with (HERE/'independent-check.json').open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
