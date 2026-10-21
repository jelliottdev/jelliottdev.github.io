"""Independent counted-quadgram verification of scorer-control evidence."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import re
import unicodedata as ud

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'experiments/records/english-scorer-controls'


def check(path):
    raw=path.read_bytes();report=json.loads(raw)
    pp=ROOT/'experiments/plans/english-scorer-language-controls.json';plan=json.loads(pp.read_bytes())
    assert report['plan_sha256']==hashlib.sha256(pp.read_bytes()).hexdigest()
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    counts={}
    for line in (HERE/'english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,number=line.split()
        assert re.fullmatch('[A-Z]{4}',gram) and gram not in counts and int(number)>0
        counts[gram]=int(number)
    total=sum(counts.values())
    assert report['model_total_count']==total and report['model_quadgrams']==len(counts)
    assert report['threshold']==plan['threshold']
    def score(text):
        grams=Counter(text[i:i+4] for i in range(len(text)-3))
        return math.fsum(n*math.log10(counts.get(g,0.01)/total) for g,n in grams.items())/sum(grams.values())
    def near(a,b):assert math.isclose(a,b,rel_tol=0,abs_tol=plan['absolute_score_tolerance']),(a,b)
    norms=[];expected_keys=[];by_key={}
    for row in report['cells']:
        key=(row['language'],row['block'],row['representation'],row['length'])
        assert key not in by_key;by_key[key]=row
    for li,code in enumerate(plan['languages']):
        lines=(ROOT/f'experiments/records/parallel-languages/{code}.devtest.txt').read_text(encoding='utf-8').splitlines()
        assert len(lines)==1012
        start=0
        for bi,n in enumerate(plan['block_sentence_counts']):
            text=' '.join(lines[start:start+n]);upper=text.upper()
            for ri,mode in enumerate(plan['representations']):
                intermediate=upper if mode=='ascii' else ''.join(c for c in ud.normalize('NFD',upper) if ud.category(c)[0]!='M')
                cleaned=re.sub('[^A-Z]','',intermediate)
                norms.append({'language':code,'block':bi,'representation':mode,'sentence_start':start,'sentence_end_exclusive':start+n,
                    'source_characters':len(text),'uppercase_characters':len(upper),'after_decomposition_characters':len(intermediate),
                    'retained_letters':len(cleaned),'discarded_letters':dict(Counter(c for c in intermediate if c.isalpha() and not re.fullmatch('[A-Z]',c)))})
                assert len(cleaned)>=max(plan['lengths'])
                for ni,length in enumerate(plan['lengths']):
                    key=(code,bi,mode,length);expected_keys.append(key);row=by_key[key];excerpt=cleaned[:length]
                    assert row['excerpt']==excerpt
                    assert row['sentence_start']==start and row['sentence_end_exclusive']==start+n
                    assert row['excerpt_sha256']==hashlib.sha256(excerpt.encode('ascii')).hexdigest()
                    original=score(excerpt);near(row['score'],original)
                    assert row['accepted']==(original>=plan['threshold'])
                    assert len(row['shuffles'])==plan['shuffle_replicates']
                    values=[]
                    for j,saved in enumerate(row['shuffles']):
                        seed=3301000+100000*li+10000*bi+1000*ri+100*ni+j
                        assert saved['seed']==seed and saved['replicate']==j
                        chars=list(excerpt);random.Random(seed).shuffle(chars);shuffled=''.join(chars)
                        assert Counter(shuffled)==Counter(excerpt)
                        assert saved['text_sha256']==hashlib.sha256(shuffled.encode('ascii')).hexdigest()
                        v=score(shuffled);near(v,saved['score']);values.append(v)
                        assert saved['accepted']==(v>=plan['threshold'])
                    summary=row['shuffle_summary']
                    near(summary['minimum'],min(values));near(summary['maximum'],max(values));near(summary['mean'],math.fsum(values)/len(values))
                    # Confirm comparison counts using independently computed scores.
                    assert summary['below_original']==sum(v<original for v in values)
                    assert summary['equal_original']==sum(v==original for v in values)
                    assert summary['above_original']==sum(v>original for v in values)
            start+=n
    assert report['normalizations']==norms
    assert list(by_key)==expected_keys and len(by_key)==384
    return {'status':'independent source and counted-quadgram check passed; human review pending','cells_checked':384,
            'shuffle_scores_checked':7680,'report_sha256':hashlib.sha256(raw).hexdigest(),
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    if a.receipt.exists():p.error('Receipt already exists')
    result=check(a.report);a.receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result))
