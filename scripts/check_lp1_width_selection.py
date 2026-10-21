"""Independently replay source lengths, shuffles and every direct column score."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def check(path):
    report = json.loads(path.read_bytes())
    plan_path = ROOT / 'experiments/plans/lp1-width-selection.json'
    plan = json.loads(plan_path.read_bytes())
    assert report['plan'] == plan
    assert report['plan_sha256'] == hashlib.sha256(plan_path.read_bytes()).hexdigest()
    for name,digest in plan['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
    assert report['producer_sha256'] == hashlib.sha256((ROOT/'scripts/lp1_width_selection.py').read_bytes()).hexdigest()
    baseline = json.loads((ROOT/'experiments/records/lp1-word-length-balance/plan.json').read_bytes())
    alphabet = set('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ')
    lengths = []
    for section in baseline['sections']:
        source = ''
        for page in section['pages']:
            name = f'text/{page}.txt'
            raw = (ROOT/name).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == baseline['input_hashes'][name]
            source += ''.join(c for c in raw.decode('utf-8') if c not in '/\r\n')
        length = 0
        for i,c in enumerate(source):
            if c in alphabet:
                length += 1
            elif c == "'" and length and i+1 < len(source) and source[i+1] in alphabet:
                continue
            elif length:
                lengths.append(length)
                length = 0
        if length: lengths.append(length)
    assert lengths == json.loads((ROOT/'experiments/records/lp1-word-length-balance/submitted-lengths.json').read_bytes())['lengths']
    assert report['source_sha256'] == baseline['input_hashes']
    n,total = len(lengths),sum(lengths)
    assert report['words'] == n == 464 and report['runes'] == total
    widths = plan['widths']
    assert report['widths'] == widths == [2,4,8,16,32,64]
    dispersion = sum(x*x for x in lengths) - Fraction(total*total,n)
    expectations = [Fraction(k-1,n-1)*dispersion for k in widths]
    assert report['column_sizes'] == [[len(lengths[j::k]) for j in range(k)] for k in widths]

    def scores(values):
        out = []
        for k,expected in zip(widths,expectations):
            columns = [values[j::k] for j in range(k)]
            imbalance = sum(Fraction(sum(c)**2,len(c)) for c in columns) - Fraction(total*total,n)
            out.append(imbalance/expected)
        return out

    observed = scores(lengths)
    assert [str(x) for x in observed] == report['observed_R']
    assert observed == [Fraction(a,b) for a,b in zip(report['observed_numerators'],report['denominators'])]
    best = min(observed)
    assert [best.numerator,best.denominator] == report['observed_minimum']
    assert [k for k,v in zip(widths,observed) if v == best] == report['observed_winning_widths']
    assert len(report['null_numerators']) == len(report['null_minima']) == len(report['null_winning_widths']) == plan['trials']
    rng = random.Random(plan['seed'])
    tails = [0]*len(widths)
    selected_tail = 0
    for trial in range(plan['trials']):
        shuffled = lengths.copy()
        for j in range(n-1,0,-1):
            swap = rng.randrange(j+1)
            shuffled[j],shuffled[swap] = shuffled[swap],shuffled[j]
        values = scores(shuffled)
        assert values == [Fraction(a,b) for a,b in zip(report['null_numerators'][trial],report['denominators'])],trial
        minimum = min(values)
        assert [minimum.numerator,minimum.denominator] == report['null_minima'][trial],trial
        assert [k for k,v in zip(widths,values) if v == minimum] == report['null_winning_widths'][trial],trial
        selected_tail += minimum <= best
        tails = [count + (value <= threshold) for count,value,threshold in zip(tails,values,observed)]
    assert tails == report['fixed_width_tails'] and selected_tail == report['selected_tail']
    assert [str(Fraction(t+1,plan['trials']+1)) for t in tails] == report['fixed_width_p']
    assert str(Fraction(selected_tail+1,plan['trials']+1)) == report['selected_p']
    return {'status':'passed','null_width_scores_checked':len(widths)*plan['trials'],
            'observed_widths_checked':len(widths),'selected_tail':selected_tail,'selected_p':report['selected_p'],
            'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--receipt',type=Path,required=True)
    args = parser.parse_args()
    if args.receipt.exists(): parser.error('Use a new receipt path')
    receipt = check(args.report)
    with args.receipt.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,indent=2)
        stream.write('\n')
    print(json.dumps(receipt,indent=2))
