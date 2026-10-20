"""Replay a pinned, selected 27x27 route; do not infer a traversal or plaintext."""
import argparse
from collections import Counter
from functools import lru_cache
from itertools import product
from math import gcd
from pathlib import Path
import hashlib,json,random
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
NAMES='F U TH O R C G W H N I J EO P X S T B E M L NG OE D A AE Y IA EA'.split()
@lru_cache(None)
def phi(n):
    if n<1: raise ValueError('Totient zero is outside this experiment')
    return sum(gcd(n,k)==1 for k in range(1,n+1))
@lru_cache(None)
def mu(n):
    if n<1: raise ValueError('Mobius zero is outside this experiment')
    count=0;p=2
    while p*p<=n:
        if n%p==0:
            n//=p;count+=1
            if n%p==0:return 0
        p+=1
    return (-1)**(count+(n>1))
def sig(key):return [mu(phi(x)) for x in key]
def n0(cell):r,c=cell;return 27*(r-1)+c
def n1(cell):r,c=cell;return 27*(c-1)+28-r
def n3(cell):r,c=cell;return 27*(27-c)+r
def axis(cells):
    r,c=cells[0];s,t=cells[-1]
    return 'horizontal' if r==s else 'vertical' if c==t else 'diagonal'
def mirror_count(grid):
    total=0
    for r in range(27):
      for c in range(27):
       for dr,dc in ((0,1),(1,0),(1,1),(1,-1)):
        for radius in range(1,14):
         a,b=r-dr*radius,c-dc*radius;d,e=r+dr*radius,c+dc*radius
         if 0<=a<27 and 0<=b<27 and 0<=d<27 and 0<=e<27:
          total+=grid[a*27+b]==grid[d*27+e]
    return total

def build():
    source=json.loads((HERE/'route.json').read_text(encoding='utf-8'))
    alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
    lookup={x['rune']:i for i,x in enumerate(alphabet)}
    grid=[];page_counts=[]
    for i in range(3):
      values=[lookup[x] for x in (ROOT/f'text/lp2-{i:02}.txt').read_text(encoding='utf-8-sig') if x in lookup]
      page_counts.append(len(values));grid+=values
    assert len(grid)==729 and grid==source['map_indices']
    results=[]
    for b in source['blocks']:
      node=[grid[n0(cell)-1] for cell in [b['node_outer_cells'][0],b['node_center'],b['node_outer_cells'][1]]]
      k=[node[0],phi(node[1]) if b['center_transform'] else node[1],node[2]]
      assert k==b['key'],b['label']
      signature=sig(k);phase=sum(signature)%3;aligned=k[phase:]+k[:phase]
      trace=[]
      for i,row in enumerate(b['rows']):
        c=grid[n0(row['cell'])-1];v=(c-aligned[i%3])%29
        assert (c,aligned[i%3],v)==(row['cipher'],row['aligned_key'],row['plaintext']),b['label']
        trace.append(dict(cell=row['cell'],cipher=c,key=aligned[i%3],output=v))
      alternatives=[]
      for p in range(3):
        shifted=k[p:]+k[:p];out=[(x['cipher']-shifted[i%3])%29 for i,x in enumerate(trace)]
        alternatives.append(dict(phase=p,tokens=[NAMES[x] for x in out]))
      results.append(dict(label=b['label'],primary=b['primary'],key=k,signature=signature,phase=phase,node_center=b['node_center'],tokens=[NAMES[x['output']] for x in trace],trace=trace,phase_ablations=alternatives))
    primary=[x for x in results if x['primary']];S=0;a=0;transitions=[]
    for current,nxt in zip(primary,primary[1:]):
      cells=[x['cell'] for x in current['trace']];begin,end=cells[0],cells[-1];center=current['node_center']
      reflected=7<=S<21;offset=1 if S<7 or 14<=S<21 else 0
      phase=(offset+sum(mu(730-n0(x) if reflected else n0(x)) for x in cells))%3
      m=min(map(n1,cells));a=(a+mu(m))%2;middle=(phase-2*a)%3;prediction=[a,-1 if middle==2 else middle,a]
      score=mu(730-n0(begin)+n0(center))+mu(gcd(n1(end),730-n0(end)))
      predicted_axis='horizontal' if score==0 else 'vertical' if score>0 else 'diagonal'
      boundary=(mu(n3(end))+phi(grid[n0(center)-1]))%2
      next_cells=[x['cell'] for x in nxt['trace']];selected=min(next_cells,key=n1);observed_boundary=int(selected==next_cells[0])
      transitions.append(dict(current=current['label'],next=nxt['label'],cumulative_before=S,mode=('reflected' if reflected else 'direct')+f'+{offset}',predicted_signature=prediction,observed_signature=nxt['signature'],signature_match=prediction==nxt['signature'],axis_score=score,predicted_axis=predicted_axis,observed_axis=axis(next_cells),axis_match=predicted_axis==axis(next_cells),predicted_boundary=boundary,observed_boundary=observed_boundary,boundary_match=boundary==observed_boundary))
      S+=phase
    # Signature is a lossy constraint: enumerate all positive-index ordered triples.
    counts=Counter(tuple(sig(k)) for k in product(range(1,29),repeat=3))
    # Same SOON derived key, three explicitly documented original centers.
    soon=next(x for x in primary if x['label']=='SOON 1');B=soon['trace'][0]['cell'];E=soon['trace'][-1]['cell'];variants=[]
    for center in [(25,7),(20,15),(25,14)]:
      score=mu(730-n0(B)+n0(center))+mu(gcd(n1(E),730-n0(E)))
      variants.append(dict(center=center,center_index=grid[n0(center)-1],transformed_center=phi(grid[n0(center)-1]),axis_score=score,next_axis='horizontal' if score==0 else 'vertical' if score>0 else 'diagonal'))
    # A mirror-count control only: frequency-preserving shuffles, no language scoring.
    rng=random.Random(3301);control=[]
    for _ in range(99):
      shuffled=grid.copy();rng.shuffle(shuffled);control.append(mirror_count(shuffled))
    used=Counter(n0(t['cell']) for b in primary for t in b['trace'])
    report=dict(source_commit=source['commit'],page_rune_counts=page_counts,map_matches=True,blocks=results,primary_blocks=len(primary),primary_output_runes=sum(used.values()),unique_ciphertext_cells=len(used),reused_cells=[dict(cell=[(n-1)//27+1,(n-1)%27+1],uses=v) for n,v in sorted(used.items()) if v>1],transitions=transitions,signature_candidates=[dict(signature=list(k),ordered_positive_index_triples=v) for k,v in sorted(counts.items()) if k[0]==k[2] and k[0] in (0,1)],soon_node_variants=variants,mirror_control=dict(definition='Equal outer runes, any center, four axes, radii 1..13, in bounds. No center transform or language test.',observed=mirror_count(grid),seed=3301,shuffles=control,minimum=min(control),maximum=max(control),mean=sum(control)/len(control)),limits=['Recorded route supplied as input, not rediscovered.','Phase thresholds 7 and 14 were fitted on this route, not held out.','No probability of intended plaintext or arbitrary-sentence construction inferred.','Positive-index key count excludes F=0; not a count of reachable geometric nodes.','Source punctuation and word boundaries are editorial, not recovered rune symbols.'])
    return report,grid

def figure(report,grid):
    used={n0(t['cell']) for b in report['blocks'] if b['primary'] for t in b['trace']}
    s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 780" role="img" aria-labelledby="title desc"><title id="title">Selected ciphertext on the 27 by 27 map</title><desc id="desc">Blue cells are used in the primary proposed reading; all other cells remain outside that reading. Numbers are one-based coordinates.</desc><rect width="700" height="780" fill="#fff"/><g font-family="sans-serif" fill="#243842"><text x="24" y="30" font-size="23">Where the proposed reading uses the map</text><text x="24" y="56" font-size="15">LP2-00–02, row-major; headings retained, separators removed</text>']
    for i in range(27):
      s.append(f'<text x="{49+i*23}" y="85" font-size="10" text-anchor="middle">{i+1}</text><text x="20" y="{103+i*23}" font-size="10">{i+1}</text>')
    for i,v in enumerate(grid):
      x=38+(i%27)*23;y=90+(i//27)*23;active=i+1 in used
      s.append(f'<rect x="{x}" y="{y}" width="22" height="22" fill="{"#d5e7ef" if active else "#f5f5f1"}"/><text x="{x+11}" y="{y+15}" font-size="9" text-anchor="middle" fill="{"#174f69" if active else "#686e70"}">{NAMES[v]}</text>')
    s.append(f'<text x="24" y="740" font-size="17">{report["unique_ciphertext_cells"]} of 729 cells used · {report["primary_output_runes"]} output runes · 17 selected blocks</text><text x="24" y="765" font-size="14">Blue shows ciphertext coverage, not all key nodes or navigation landmarks.</text></g></svg>')
    return '\n'.join(s)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    r,g=build();outputs={ROOT/'exports/totient-map-route.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n',ROOT/'exports/figures/totient-map-coverage.svg':figure(r,g)}
    for p,text in outputs.items():
      if args.check:assert p.read_text(encoding='utf-8')==text,p
      else:p.write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({k:r[k] for k in ['primary_blocks','primary_output_runes','unique_ciphertext_cells','soon_node_variants','signature_candidates']}))
    print('Transition matches:',{k:sum(x[k] for x in r['transitions']) for k in ['signature_match','axis_match','boundary_match']})
    print('Mirrors:',r['mirror_control']['observed'],'shuffle range',r['mirror_control']['minimum'],r['mirror_control']['maximum'])
if __name__=='__main__':main()
