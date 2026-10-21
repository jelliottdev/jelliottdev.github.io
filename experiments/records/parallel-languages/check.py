"""Independent regex tokenization, integer-count and ranking checks; no network."""
from collections import Counter
import json
from math import comb, isclose
from pathlib import Path
import re
import unicodedata

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def words(text,mode):
    text=unicodedata.normalize('NFC',text.lower())
    if mode in ('folded','gp-length'):
        text=''.join(c for c in unicodedata.normalize('NFD',text) if unicodedata.category(c)[0]!='M')
    letters=''.join(sorted(set(c for c in text if c.isalpha())))
    atom='['+re.escape(letters)+']'
    tokens=re.findall(atom+'+(?:[\'\u2019]'+atom+'+)*',text)
    groups=['ing','th','eo','ng','oe','ae','ia','io','ea'] if mode=='gp-length' else ['ch','dd','ff','ng','ll','ph','rh','th'] if mode=='welsh-digraph' else []
    pattern='|'.join(groups+['.'])
    result=[]
    for token in tokens:
        units=re.findall(pattern,token.replace("'",'').replace('\u2019',''))
        if mode=='gp-length':units=[{'ing':'ng','io':'ia','k':'c','z':'s'}.get(x,x) for x in units]
        result.append(units)
    return result


def check_stats(tokens,saved):
    assert len(tokens)==saved['tokens']
    h=Counter(min(len(t),16) for t in tokens)
    assert [h[i] for i in range(1,17)]==saved['histogram']
    counts=Counter(x for t in tokens for x in t)
    n=sum(counts.values())
    assert n==saved['units'] and dict(counts)==saved['symbol_counts']
    assert len(counts)==saved['distinct']
    assert isclose(sum(comb(x,2) for x in counts.values())/comb(n,2),saved['ioc'],abs_tol=1e-14)
    equal=sum(t[i]==t[i+1] for t in tokens for i in range(len(t)-1))
    pairs=n-len(tokens)
    assert equal==saved['equal_pairs'] and pairs==saved['adjacent_pairs']
    assert isclose(equal/pairs,saved['adjacent_equal'],abs_tol=1e-14)


def main():
    r=json.loads((HERE/'results.json').read_bytes())
    ledger=json.loads((ROOT/'exports/unsolved-word-tokens.json').read_bytes())
    check_stats([list(t['token'].replace("'",'')) for t in ledger],r['target'])
    for mode,data in r['modes'].items():
        for row in data['ranking']:
            text=(HERE/(row['code']+'.devtest.txt')).read_text(encoding='utf-8')
            check_stats(words(text,mode),row)
            a=r['target']['histogram'];b=row['histogram']
            numerator=sum(abs(x*sum(b)-y*sum(a)) for x,y in zip(a,b))
            assert isclose(numerator/(2*sum(a)*sum(b)),row['length_tv'],abs_tol=1e-14)
        assert data['ranking']==sorted(data['ranking'],key=lambda x:x['length_tv'])
    check_stats(words((HERE/'cym_Latn.devtest.txt').read_text(encoding='utf-8'),'welsh-digraph'),r['welsh_digraph_sensitivity'])
    # Hand-check conventions and the distinction between a rune label and a letter.
    assert words("can't l\u2019arbre co-op",'letters')==[list('cant'),list('larbre'),list('co'),list('op')]
    assert words('thing singing', 'gp-length')==[['th','ng'],['s','ng','ng']]
    assert words('llan dd ff', 'welsh-digraph')==[['ll','a','n'],['dd'],['ff']]
    print('PASS: independent tokenization, counts, IoC, doublets, exact TV fractions and ordering for 24 profiles, Welsh digraphs and target')


if __name__=='__main__':main()
