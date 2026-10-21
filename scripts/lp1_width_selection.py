"""Run the frozen six-width selection comparison, using exact scores."""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
from math import lcm
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'experiments/plans/lp1-width-selection.json'


def run():
    plan = json.loads((ROOT / PLAN).read_bytes())
    for path, digest in plan['input_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    spec = importlib.util.spec_from_file_location('baseline', ROOT / 'experiments/records/lp1-word-length-balance/run.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    base_plan = json.loads((ROOT / 'experiments/records/lp1-word-length-balance/plan.json').read_bytes())
    words, _ = baseline.reconstruct(base_plan)
    assert words == json.loads((ROOT / 'experiments/records/lp1-word-length-balance/words.json').read_bytes())
    values = [word['rune_length'] for word in words]
    assert values == json.loads((ROOT / 'experiments/records/lp1-word-length-balance/submitted-lengths.json').read_bytes())['lengths']
    n, total = len(values), sum(values)
    assert n == 464
    dispersion = n * sum(v*v for v in values) - total*total
    widths = plan['widths']
    assert widths == [2,4,8,16,32,64]
    sizes = [[len(values[j::k]) for j in range(k)] for k in widths]
    multiples = [lcm(*counts) for counts in sizes]
    denominators = [(k-1)*m*dispersion for k,m in zip(widths,multiples)]

    def scores(sequence):
        sums = [sum(sequence[j::64]) for j in range(64)]
        out = []
        for k, counts, multiple in reversed(list(zip(widths,sizes,multiples))):
            assert len(sums) == k
            out.append((n*sum(s*s*(multiple//count) for s,count in zip(sums,counts)) - total*total*multiple)*(n-1))
            sums = [sums[j] + sums[j+k//2] for j in range(k//2)]
        return out[::-1]

    def select(row):
        winner = 0
        for i in range(1,len(widths)):
            if row[i]*denominators[winner] < row[winner]*denominators[i]:
                winner = i
        ties = [widths[i] for i in range(len(widths)) if row[i]*denominators[winner] == row[winner]*denominators[i]]
        value = Fraction(row[winner],denominators[winner])
        return [value.numerator,value.denominator], ties

    observed = scores(values)
    selected, winning_widths = select(observed)
    rng = random.Random(plan['seed'])
    rows, minima, winners = [], [], []
    for _ in range(plan['trials']):
        shuffled = values.copy()
        rng.shuffle(shuffled)
        row = scores(shuffled)
        minimum, ties = select(row)
        rows.append(row)
        minima.append(minimum)
        winners.append(ties)
    fixed_tails = [sum(row[i] <= observed[i] for row in rows) for i in range(len(widths))]
    selected_tail = sum(a*selected[1] <= selected[0]*b for a,b in minima)
    base_result = json.loads((ROOT / 'experiments/records/lp1-word-length-balance/results.json').read_bytes())
    assert Fraction(observed[3],denominators[3]) == Fraction(base_result['R_fraction'])
    assert fixed_tails[3] == base_result['lower_tail_with_ties'] == 54
    return {'plan':plan, 'plan_sha256':hashlib.sha256((ROOT/PLAN).read_bytes()).hexdigest(),
            'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'words':n, 'runes':total, 'widths':widths, 'column_sizes':sizes,
            'score_encoding':'R = integer numerator / width-specific denominator',
            'denominators':denominators, 'observed_numerators':observed,
            'observed_R':[str(Fraction(a,b)) for a,b in zip(observed,denominators)],
            'observed_minimum':selected, 'observed_winning_widths':winning_widths,
            'fixed_width_tails':fixed_tails,
            'fixed_width_p':[str(Fraction(t+1,plan['trials']+1)) for t in fixed_tails],
            'selected_tail':selected_tail, 'selected_p':str(Fraction(selected_tail+1,plan['trials']+1)),
            'null_numerators':rows, 'null_minima':minima, 'null_winning_widths':winners,
            'source_sha256':base_plan['input_hashes']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error('Use a new output file')
    result = run()
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['observed_R','observed_minimum','observed_winning_widths','fixed_width_tails','selected_tail','selected_p']},indent=2))
