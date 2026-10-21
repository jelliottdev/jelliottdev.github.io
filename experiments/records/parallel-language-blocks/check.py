"""Independently reconstruct block histograms and nearest-reference decisions."""
from collections import Counter
from fractions import Fraction
import importlib.util
import json
from math import isclose
from pathlib import Path

HERE=Path(__file__).resolve().parent;BASE=HERE.parent/'parallel-languages';ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('independent_tokenizer',BASE/'check.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)


def hist(words):
    c=Counter(min(len(w),16) for w in words);return [c[i] for i in range(1,17)]


def distance(a,b):
    return sum(abs(Fraction(x,sum(a))-Fraction(y,sum(b))) for x,y in zip(a,b))/2


def main():
    saved=json.loads((HERE/'results.json').read_bytes())
    codes=list(json.loads((BASE/'plan.json').read_bytes())['languages'])
    target=Counter(min(x['rune_length'],16) for x in json.loads((ROOT/'exports/unsolved-word-tokens.json').read_bytes()))
    target=[target[i] for i in range(1,17)]
    seen=[]
    for a,b in saved['sentence_ranges_one_based_inclusive']:seen.extend(range(a,b+1))
    assert seen==list(range(1,1013))
    for mode,data in saved['modes'].items():
        refs={c:hist(helper.words((BASE/f'{c}.dev.txt').read_text(encoding='utf-8'),mode)) for c in codes}
        confusion={c:{d:0 for d in codes} for c in codes};winners=Counter()
        for (a,b),block in zip(saved['sentence_ranges_one_based_inclusive'],data['blocks']):
            assert len(block['ranking'])==8
            for row in block['ranking']:
                code=row['code'];lines=(BASE/f'{code}.devtest.txt').read_text(encoding='utf-8').splitlines()[a-1:b]
                tokens=[w for line in lines for w in helper.words(line,mode)];h=hist(tokens)
                assert len(tokens)==row['tokens'] and h==row['histogram']
                assert isclose(float(distance(target,h)),row['length_tv'],abs_tol=1e-14)
                decisions=sorted((distance(h,r),c) for c,r in refs.items())
                assert decisions[0][1]==row['control_nearest']
                for (actual,c),(value,d) in zip(decisions,row['control_distances']):
                    assert c==d and isclose(float(actual),value,abs_tol=1e-14)
                confusion[code][decisions[0][1]]+=1
            assert block['ranking']==sorted(block['ranking'],key=lambda x:x['length_tv'])
            winners[block['ranking'][0]['language']]+=1
        assert confusion==data['confusion'] and dict(winners)==data['manuscript_best_counts']
        assert sum(confusion[c][c] for c in codes)==data['correct']
    print('PASS: all 192 block profiles and reference decisions; independent tokenizer and rational distances')


if __name__=='__main__':main()
