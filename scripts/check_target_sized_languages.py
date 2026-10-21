"""Rebuild exact-token language controls independently from source text."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import unicodedata as ud

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/records/parallel-languages'


def lengths(line,mode):
    text=ud.normalize('NFC',line.lower())
    if mode!='letters':
        text=''.join(c for c in ud.normalize('NFD',text) if ud.category(c)[0]!='M')
    alphabet=''.join(sorted({c for c in text if c.isalpha()}))
    if not alphabet: return []
    atom='['+re.escape(alphabet)+']'
    tokens=re.findall(atom+"+(?:['\u2019]"+atom+'+)*',text)
    result=[]
    for token in tokens:
        token=token.replace("'",'').replace('\u2019','')
        result.append(len(re.findall('ing|th|eo|ng|oe|ae|ia|io|ea|.',token)) if mode=='gp-length' else len(token))
    return result


def histogram(values):
    out=[0]*16
    for v in values: out[min(v,16)-1]+=1
    return out


def score(a,b):
    n,m=sum(a),sum(b)
    return Fraction(sum(abs(x*m-y*n) for x,y in zip(a,b)),2*n*m)


def encoded(f): return {'numerator':f.numerator,'denominator':f.denominator}


def verify(report):
    planpath=ROOT/'experiments/plans/target-sized-language-controls.json'
    plan=json.loads(planpath.read_bytes())
    assert report['plan_sha256']==hashlib.sha256(planpath.read_bytes()).hexdigest()
    amendment=ROOT/'experiments/plans/target-sized-language-controls-amendment.md'
    assert report['amendment_sha256']==hashlib.sha256(amendment.read_bytes()).hexdigest()
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    target=histogram([sum(c!="'" for c in t['token']) for t in json.loads((ROOT/'exports/unsolved-word-tokens.json').read_bytes())])
    size=plan['tokens_per_block']
    assert sum(target)==size==report['tokens_per_block']==2896
    assert report['target_histogram']==target
    assert set(report['modes'])==set(plan['modes'])
    boundaries={}; checked=0
    for mode in plan['modes']:
        data=report['modes'][mode]; references={}; streams={}
        for code in plan['languages']:
            for split in ('dev','devtest'):
                tokens=[]
                for sentence,line in enumerate((BASE/f'{code}.{split}.txt').read_text(encoding='utf-8').splitlines()):
                    tokens.extend((n,sentence,i) for i,n in enumerate(lengths(line,mode)))
                if split=='dev': references[code]=histogram(t[0] for t in tokens)
                else: streams[code]=tokens
        assert data['references']==references
        td={c:score(target,h) for c,h in references.items()}
        assert data['target_distances']=={c:encoded(v) for c,v in td.items()}
        assert data['target_nearest']==[c for c,v in td.items() if v==min(td.values())]
        assert set(data['languages'])==set(plan['languages'])
        for code,tokens in streams.items():
            boundaries[code,mode]=[t[1:] for t in tokens]
            saved=data['languages'][code]; n=len(tokens)//size
            assert saved['total_tokens']==len(tokens)
            assert saved['complete_blocks']==len(saved['blocks'])==n
            assert saved['remainder']=={'token_start':n*size,'token_end_exclusive':len(tokens),'count':len(tokens)-n*size}
            own=[]; wins=Counter(); decisions=Counter()
            for i,block in enumerate(saved['blocks']):
                sample=tokens[i*size:(i+1)*size]
                h=histogram(t[0] for t in sample)
                distances={c:score(h,ref) for c,ref in references.items()}
                best=[c for c,d in distances.items() if d==min(distances.values())]
                expected={'index':i,'token_start':i*size,'token_end_exclusive':(i+1)*size,
                          'first_sentence_token':list(sample[0][1:]),'last_sentence_token':list(sample[-1][1:]),
                          'histogram':h,'distances':{c:encoded(d) for c,d in distances.items()},'nearest':best,
                          'true_language_margin':encoded(min(d for c,d in distances.items() if c!=code)-distances[code])}
                assert block==expected,(mode,code,i)
                decisions['ties' if len(best)>1 else 'unique_correct' if best==[code] else 'unique_wrong']+=1
                wins.update(best); own.append(distances[code]); checked+=1
            assert all(saved[k]==decisions[k] for k in ('ties','unique_correct','unique_wrong'))
            assert saved['nearest_tally']==dict(wins)
            assert saved['true_language_distance_range']=={'minimum':encoded(min(own)),'maximum':encoded(max(own))}
    expected={c:{'letters_equal_folded':boundaries[c,'letters']==boundaries[c,'folded'],
                 'folded_equal_gp':boundaries[c,'folded']==boundaries[c,'gp-length']} for c in plan['languages']}
    assert report['representation_boundaries']==expected
    assert all(v['folded_equal_gp'] for v in expected.values())
    return checked


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--receipt',required=True,type=Path)
    args=parser.parse_args()
    if args.receipt.exists():parser.error('Receipt already exists')
    raw=args.report.read_bytes(); checked=verify(json.loads(raw))
    receipt={'status':'source reconstruction passed; human review pending','block_profiles':checked,
             'report_sha256':hashlib.sha256(raw).hexdigest(),
             'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt))
