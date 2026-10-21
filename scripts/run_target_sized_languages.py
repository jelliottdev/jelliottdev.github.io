"""Frozen exact-token control; offline, standard library, no language posterior."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'experiments/records/parallel-languages'
PLAN = ROOT/'experiments/plans/target-sized-language-controls.json'
AMENDMENT = ROOT/'experiments/plans/target-sized-language-controls-amendment.md'


def histogram(lengths):
    bins = Counter(min(n,16) for n in lengths)
    return [bins[i] for i in range(1,17)]


def distance(a,b):
    return sum((abs(Fraction(x,sum(a))-Fraction(y,sum(b))) for x,y in zip(a,b)),Fraction())/2


def rational(x):
    return {'numerator':x.numerator,'denominator':x.denominator}


def produce():
    plan = json.loads(PLAN.read_bytes())
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256']
    spec = importlib.util.spec_from_file_location('baseline_language', SOURCE/'run.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    ledger = json.loads((ROOT/'exports/unsolved-word-tokens.json').read_bytes())
    target = histogram([len(t['token'].replace("'",'')) for t in ledger])
    size = plan['tokens_per_block']
    assert sum(target) == size == 2896
    result = {'status':'producer result; independent verification pending',
              'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
              'amendment_sha256':hashlib.sha256(AMENDMENT.read_bytes()).hexdigest(),
              'target_histogram':target,'tokens_per_block':size,'modes':{}}
    endpoints = {}
    for mode in plan['modes']:
        references, streams = {}, {}
        for code in plan['languages']:
            for split in ('dev','devtest'):
                tokens = [(len(w),line_index,word_index)
                          for line_index,line in enumerate((SOURCE/f'{code}.{split}.txt').read_text(encoding='utf-8').splitlines())
                          for word_index,w in enumerate(baseline.tokenize(line,mode))]
                if split == 'dev':
                    references[code] = histogram([t[0] for t in tokens])
                else:
                    streams[code] = tokens
        target_distances = {c:distance(target,h) for c,h in references.items()}
        minimum = min(target_distances.values())
        data = {'references':references,'target_distances':{c:rational(d) for c,d in target_distances.items()},
                'target_nearest':[c for c,d in target_distances.items() if d==minimum], 'languages':{}}
        for code,tokens in streams.items():
            boundary_list = [(t[1],t[2]) for t in tokens]
            if mode == 'gp-length':
                assert endpoints[(code,'folded')] == boundary_list
            endpoints[(code,mode)] = boundary_list
            blocks, tally, correct, wrong, ties, own = [], Counter(), 0, 0, 0, []
            complete = len(tokens)//size
            for block in range(complete):
                start,end = block*size,(block+1)*size
                selected = tokens[start:end]
                hist = histogram([t[0] for t in selected])
                ds = {c:distance(hist,h) for c,h in references.items()}
                best = min(ds.values()); nearest = [c for c,d in ds.items() if d==best]
                margin = min(d for c,d in ds.items() if c!=code)-ds[code]
                if len(nearest)>1: ties+=1
                elif nearest==[code]: correct+=1
                else: wrong+=1
                tally.update(nearest); own.append(ds[code])
                blocks.append({'index':block,'token_start':start,'token_end_exclusive':end,
                               'first_sentence_token':list(selected[0][1:]),'last_sentence_token':list(selected[-1][1:]),
                               'histogram':hist,'distances':{c:rational(d) for c,d in ds.items()},
                               'nearest':nearest,'true_language_margin':rational(margin)})
            assert complete > 0
            data['languages'][code] = {'total_tokens':len(tokens),'complete_blocks':complete,
                'remainder':{'token_start':complete*size,'token_end_exclusive':len(tokens),'count':len(tokens)%size},
                'unique_correct':correct,'unique_wrong':wrong,'ties':ties,'nearest_tally':dict(sorted(tally.items())),
                'true_language_distance_range':{'minimum':rational(min(own)),'maximum':rational(max(own))},'blocks':blocks}
        result['modes'][mode] = data
    result['representation_boundaries'] = {
        code:{'letters_equal_folded':endpoints[(code,'letters')]==endpoints[(code,'folded')],
              'folded_equal_gp':endpoints[(code,'folded')]==endpoints[(code,'gp-length')]}
        for code in plan['languages']}
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Choose a new output path to preserve evidence')
    result=produce()
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({mode:{code:{k:d[k] for k in ('complete_blocks','unique_correct','unique_wrong','ties')} for code,d in data['languages'].items()} for mode,data in result['modes'].items()}))
