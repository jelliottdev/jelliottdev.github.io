"""Test whether LP2 doublets cluster at page-anchored block boundaries."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SIZES = range(2, 30)
TRIALS = 3000
SEED = 330107


def load():
    index_raw = (ROOT/'data/index.json').read_bytes()
    index = json.loads(index_raw)
    lookup = {item['rune']: item['index'] for item in index['alphabet']}
    assert len(lookup) == 29
    hashes = {'data/index.json': hashlib.sha256(index_raw).hexdigest()}
    pages = []
    for number in range(56):
        path = f'text/lp2-{number:02d}.txt'
        raw = (ROOT/path).read_bytes()
        unknown = {c for c in raw.decode('utf-8') if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        if unknown:
            raise ValueError(f'Unknown rune in {path}: {unknown!r}')
        stream = [lookup[c] for c in raw.decode('utf-8') if c in lookup]
        assert len(stream) == next(p['rune_count'] for p in index['pages'] if p['id']==f'lp2-{number:02d}')
        events = [i for i in range(len(stream)-1) if stream[i] == stream[i+1]]
        pages.append({'id': f'lp2-{number:02d}', 'edges': max(0,len(stream)-1), 'events': events})
        hashes[path] = hashlib.sha256(raw).hexdigest()
    assert sum(len(p['events']) for p in pages) == 86
    return pages, hashes


def expected_variance(pages, size, phase):
    mean = variance = 0.0
    for page in pages:
        edges, event_count = page['edges'], len(page['events'])
        if edges < 2 or not event_count:
            continue
        boundary_count = edges//size if phase==0 else max(0,(edges-phase)//size+1)
        fraction = boundary_count / edges
        mean += event_count * fraction
        variance += event_count * fraction * (1-fraction) * (edges-event_count)/(edges-1)
    return mean, variance


def scores(event_positions, expectations):
    output=[]
    for size in SIZES:
        observed = Counter((position+1) % size for positions in event_positions for position in positions)
        for phase in range(size):
            mean, variance = expectations[(size,phase)]
            if variance <= 0:
                continue
            value = observed[phase]
            output.append({'size':size,'phase':phase,'matches':value,
                           'expected':round(mean,6),'z':round((value-mean)/math.sqrt(variance),6)})
    return output


def report():
    pages, hashes=load()
    positions=[page['events'] for page in pages]
    expectations={(size,phase):expected_variance(pages,size,phase)
                  for size in SIZES for phase in range(size)}
    observed=scores(positions,expectations)
    top=sorted(observed,key=lambda row:(-row['z'],row['size'],row['phase']))[:12]
    fixed=[next(row for row in observed if row['size']==size and row['phase']==0)
           for size in (5,7,13)]
    rng=random.Random(SEED)
    maxima=[]
    fixed_trials={size:[] for size in (5,7,13)}
    for _ in range(TRIALS):
        trial=[rng.sample(range(page['edges']),len(page['events'])) if page['events'] else []
               for page in pages]
        measured=scores(trial,expectations)
        maxima.append(max(row['z'] for row in measured))
        for size in fixed_trials:
            fixed_trials[size].append(next(row['matches'] for row in measured
                                           if row['size']==size and row['phase']==0))
    maxima.sort()
    return {'schema':'liberpedia-block-boundary-doublets-v1','input_sha256':hashes,
            'scope':'LP2-00–55; non-runes removed inside each page; no cross-page edges. Block counter starts at zero on every page.',
            'pages':[{'page':p['id'],'edges':p['edges'],'doublets':len(p['events']),
                      'event_edges_zero_based':p['events']} for p in pages],
            'edge_count':sum(p['edges'] for p in pages),'doublet_count':86,
            'candidate_count':len(observed),
            'all_placements':observed,
            'definition':'An edge from rune i to i+1 has phase (i+1) mod block size. Phase zero is the ordinary page-start-anchored block boundary. Nonzero phases represent one shared offset across pages.',
            'top_by_z':top,'fixed_phase_zero':[
                {**row,'matched_control_at_least_observed':sum(v>=row['matches'] for v in fixed_trials[row['size']]),
                 'control_central_95':[sorted(fixed_trials[row['size']])[int(.025*TRIALS)],
                                       sorted(fixed_trials[row['size']])[int(.975*TRIALS)-1]]}
                for row in fixed],
            'search_control':{'trials':TRIALS,'seed':SEED,
                              'model':'Choose the observed number of event edges uniformly without replacement within each page; search sizes 2–29 and every shared phase in each trial.',
                              'observed_max_z':top[0]['z'],
                              'max_z_central_95':[maxima[int(.025*TRIALS)],maxima[int(.975*TRIALS)-1]],
                              'max_z_at_least_observed':sum(value>=top[0]['z'] for value in maxima)},
            'limits':'The conditional control tests placement of existing doublets only. It does not model how a block cipher produces their low total, page-specific unknown phases, interrupts, or a key layer. The size range and page anchoring are declared after the anomaly was known.'}


def figure(data):
    rows=data['fixed_phase_zero']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 250" role="img" aria-labelledby="title desc">',
           '<title id="title">Doublets at block boundaries for sizes five, seven and thirteen</title>',
           '<desc id="desc">Observed boundary doublets are compared with fixed-count page randomization ranges. This chart does not identify a cipher.</desc>',
           '<rect width="620" height="250" fill="white"/>',
           '<g font-family="system-ui,sans-serif" fill="#27343c">',
           '<text x="18" y="27" font-size="18" font-weight="600">Doublets at block boundaries</text>',
           '<text x="18" y="47" font-size="12">Page-start anchored; 86 observed doublets across LP2-00–55</text>']
    for n,row in enumerate(rows):
        y=82+n*48
        lo,hi=row['control_central_95']
        x=lambda value:150+value*12
        parts += [f'<text x="18" y="{y+5}" font-size="14">Size {row["size"]}</text>',
                  f'<line x1="150" y1="{y}" x2="510" y2="{y}" stroke="#dce2e6" stroke-width="2"/>',
                  f'<rect x="{x(lo)}" y="{y-8}" width="{max(2,x(hi)-x(lo))}" height="16" fill="#a9bcc5"/>',
                  f'<circle cx="{x(row["matches"])}" cy="{y}" r="6" fill="#255f79"/>',
                  f'<text x="525" y="{y+5}" font-size="13">{row["matches"]}</text>']
    parts += ['<text x="150" y="235" font-size="12">0</text>',
              '<text x="447" y="235" font-size="12">30 matches</text>',
              '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report(); payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'; visual=figure(result)
    if args.write:
        (HERE/'results.json').write_text(payload,encoding='utf-8',newline='\n')
        (HERE/'boundaries.svg').write_text(visual,encoding='utf-8',newline='\n')
    if args.check:
        assert payload==(HERE/'results.json').read_text(encoding='utf-8')
        assert visual==(HERE/'boundaries.svg').read_text(encoding='utf-8')
        print('PASS block-boundary positions and matched search control')
    print('top',result['top_by_z'][0], 'fixed', result['fixed_phase_zero'],
          'selected tail',result['search_control']['max_z_at_least_observed'],'/',TRIALS)


if __name__=='__main__':main()
