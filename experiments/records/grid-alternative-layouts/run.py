"""Compare directional prime paths under three fixed layouts of the LP2 256 cells."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
TRIALS=3000
SEED=330108
TARGETS=(1033,2213,3301)
DIRECTIONS=[(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]


def prime(value):
    return value>=2 and all(value%d for d in range(2,math.isqrt(value)+1))


UNIVERSE={''.join(d) for d in itertools.product('0123',repeat=4)
          if prime(int(''.join(d),10))}


def paths(height,width,within_quadrant=False):
    output=[]
    for y in range(height):
        for x in range(width):
            for dx,dy in DIRECTIONS:
                points=[(x+i*dx,y+i*dy) for i in range(4)]
                if not all(0<=px<width and 0<=py<height for px,py in points):
                    continue
                if within_quadrant and len({(px//8,py//8) for px,py in points})!=1:
                    continue
                output.append(tuple(py*width+px for px,py in points))
    return output


LAYOUTS={'source_32x8':paths(32,8),
         'reshaped_16x16':paths(16,16),
         'four_8x8_quadrants':paths(16,16,True)}


def measure(digits,routes):
    hits=Counter()
    eligible=0
    for route in routes:
        spelling=''.join(digits[index] for index in route)
        if '4' in spelling:
            continue
        eligible+=1
        if spelling in UNIVERSE:
            hits[int(spelling,10)]+=1
    missing=sorted(int(spelling,10) for spelling in UNIVERSE if not hits[int(spelling,10)])
    return {'directed_paths':len(routes),'eligible_paths':eligible,
            'prime_occurrences':sum(hits.values()),'distinct_prime_values':len(hits),
            'missing_prime_values':missing,
            'target_occurrences':{str(value):hits[value] for value in TARGETS}}


def report():
    source_path='exports/alphanumeric-grids.json'
    raw=(ROOT/source_path).read_bytes()
    rows=json.loads(raw)['records']
    assert len(rows)==256 and [r['sequence'] for r in rows]==list(range(1,257))
    digits=[row['token'][0] for row in rows]
    assert set(digits)==set('01234')
    observed={name:measure(digits,routes) for name,routes in LAYOUTS.items()}
    baseline=json.loads((ROOT/'experiments/records/grid-prime-paths/results.json').read_text(encoding='utf-8'))
    assert observed['source_32x8']['prime_occurrences']==baseline['prime_occurrences']==191
    assert observed['source_32x8']['missing_prime_values']==baseline['missing_primes']
    rng=random.Random(SEED)
    missing_counts={name:[] for name in LAYOUTS}
    target_absent_counts={name:0 for name in LAYOUTS}
    for _ in range(TRIALS):
        shuffled=digits.copy();rng.shuffle(shuffled)
        for name,routes in LAYOUTS.items():
            result=measure(shuffled,routes)
            missing_counts[name].append(len(result['missing_prime_values']))
            target_absent_counts[name]+=all(value in result['missing_prime_values'] for value in TARGETS)
    controls={}
    for name,values in missing_counts.items():
        ordered=sorted(values)
        count=len(observed[name]['missing_prime_values'])
        controls[name]={'missing_mean':round(sum(values)/TRIALS,6),
                        'missing_central_95':[ordered[int(.025*TRIALS)],ordered[int(.975*TRIALS)-1]],
                        'missing_at_least_observed':sum(v>=count for v in values),
                        'all_three_named_targets_absent':target_absent_counts[name],
                        'missing_histogram':dict(sorted(Counter(values).items()))}
    return {'schema':'liberpedia-grid-alternative-layouts-v1',
            'input_sha256':{source_path:hashlib.sha256(raw).hexdigest(),
                            'experiments/records/grid-prime-paths/results.json':hashlib.sha256((ROOT/'experiments/records/grid-prime-paths/results.json').read_bytes()).hexdigest()},
            'scope':'Same 256 tokens in archived row-major order from LP2-49–51. Only the first digit of each token is used.',
            'rule':'Read four adjacent cells in each of eight straight directions. Reject a path containing 4. Interpret its four digits as a decimal integer, allowing leading zeroes, and retain decimal primes.',
            'layouts':{'source_32x8':'Original 32 rows by 8 columns, page rows concatenated; paths may cross page boundaries.',
                       'reshaped_16x16':'Same 256 tokens reshaped row-major into 16 rows by 16 columns; paths may cross former page boundaries.',
                       'four_8x8_quadrants':'Same 16 by 16 shape, but every path must stay entirely within one of four fixed 8 by 8 quadrants.'},
            'prime_universe_size':len(UNIVERSE),'named_targets':list(TARGETS),
            'observed':observed,
            'control':{'model':'Uniformly shuffle all 256 first digits, preserving the 0–4 frequency table; rerun every fixed layout and path rule.',
                       'trials':TRIALS,'seed':SEED,'layouts':controls},
            'limits':'The target names and alternate layouts were considered after earlier patterns were known. These descriptive controls do not give a prospective probability for those names or test a cipher, suffix letters, page artwork, or every possible layout.'}


def figure(data):
    labels={'source_32x8':'32 × 8 source','reshaped_16x16':'16 × 16 reshape','four_8x8_quadrants':'Four 8 × 8 blocks'}
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 250" role="img" aria-labelledby="title desc">',
           '<title id="title">Missing decimal-prime strings under three grid layouts</title>',
           '<desc id="desc">The original 32 by 8 layout misses three prime values. The alternative layouts have their own missing counts. Shaded ranges show global first-digit shuffle controls.</desc>',
           '<rect width="660" height="250" fill="white"/>',
           '<g font-family="system-ui,sans-serif" fill="#27343c">',
           '<text x="18" y="27" font-size="18" font-weight="600">Missing prime values by layout</text>',
           '<text x="18" y="47" font-size="12">Four-cell paths · 49 possible decimal-prime values · fixed digit counts</text>']
    for i,(name,label) in enumerate(labels.items()):
        y=85+i*48
        row=data['observed'][name];control=data['control']['layouts'][name]
        lo,hi=control['missing_central_95'];value=len(row['missing_prime_values'])
        scale=32
        parts += [f'<text x="18" y="{y+5}" font-size="13">{label}</text>',
                  f'<line x1="250" y1="{y}" x2="570" y2="{y}" stroke="#dce2e6" stroke-width="2"/>',
                  f'<rect x="{250+lo*scale}" y="{y-8}" width="{max(2,(hi-lo)*scale)}" height="16" fill="#a9bcc5"/>',
                  f'<circle cx="{250+value*scale}" cy="{y}" r="6" fill="#255f79"/>',
                  f'<text x="590" y="{y+5}" font-size="13">{value}</text>']
    parts += ['<text x="250" y="235" font-size="12">0</text>',
              '<text x="532" y="235" font-size="12">10 missing</text>',
              '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report();payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n';visual=figure(result)
    if args.write:
        (HERE/'results.json').write_text(payload,encoding='utf-8',newline='\n')
        (HERE/'layouts.svg').write_text(visual,encoding='utf-8',newline='\n')
    if args.check:
        assert payload==(HERE/'results.json').read_text(encoding='utf-8')
        assert visual==(HERE/'layouts.svg').read_text(encoding='utf-8')
        print('PASS alternate grid layouts and matched global shuffles')
    for name,row in result['observed'].items():
        print(name,row['directed_paths'],row['prime_occurrences'],row['missing_prime_values'])


if __name__=='__main__':main()
