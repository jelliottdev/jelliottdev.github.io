"""Fresh dot centroids and exact shared-radius certificate. Requires Pillow."""
import argparse
from collections import deque
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from PIL import Image, __version__ as PILLOW_VERSION

ROOT=Path(__file__).resolve().parents[3]
REPORT=ROOT/'exports/compass-shared-radii.json'
BOXES={'lp2-33':(576,1656,1824,1836),'lp2-39':(1200,1638,1800,1746)}
CORNERS=[(0,0),(2399,0),(0,3599),(2399,3599)]
DIAGONAL_SQUARED=2399**2+3599**2

def measure_dots(gray,box,threshold):
    x0,y0,x1,y1=box
    w,h=x1-x0,y1-y0
    raw=gray.crop(box).tobytes()
    remaining={i for i,p in enumerate(raw) if p<threshold}
    found=[]
    while remaining:
        seed=remaining.pop();queue=deque([seed]);xs=[];ys=[]
        while queue:
            i=queue.popleft();x,y=i%w,i//w;xs.append(x);ys.append(y)
            for j,ok in [(i-1,x>0),(i+1,x+1<w),(i-w,y>0),(i+w,y+1<h)]:
                if ok and j in remaining:
                    remaining.remove(j);queue.append(j)
        area=len(xs);bw=max(xs)-min(xs)+1;bh=max(ys)-min(ys)+1
        if area>200 and 7*bh<10*bw<13*bh and 5*area>3*bw*bh:
            sx=sum(xs)+area*x0;sy=sum(ys)+area*y0
            found.append({'area':area,'sum_x':sx,'sum_y':sy,
                          'box':[min(xs)+x0,min(ys)+y0,max(xs)+x0+1,max(ys)+y0+1]})
    found.sort(key=lambda d:F(d['sum_x'],d['area']))
    assert len(found)==3, (box,threshold,len(found))
    return found

def geometry(dots):
    a,b,c=[(F(d['sum_x'],d['area']),F(d['sum_y'],d['area'])) for d in dots]
    v=[c[i]-a[i] for i in (0,1)];v2=sum(x*x for x in v)
    t=sum((b[i]-a[i])*v[i] for i in (0,1))/v2
    q=[a[i]+t*v[i] for i in (0,1)];e=[b[i]-q[i] for i in (0,1)]
    k=t*(1-t)*v2
    errors=[2*sum(e[i]*(q[i]-x[i]) for i in (0,1))+sum(y*y for y in e) for x in CORNERS]
    return t,k,min(errors),max(errors)

def ratio(x):return {'numerator':x.numerator,'denominator':x.denominator,'decimal':float(x)}

def measure():
    pages=[];cases={t:[] for t in (100,140,180)}
    for page,box in BOXES.items():
        path=ROOT/f'images/{page}.jpg'
        with Image.open(path) as im:
            assert im.size==(2400,3600)
            gray=im.convert('RGB').convert('L')
        variants=[]
        for threshold in cases:
            dots=measure_dots(gray,box,threshold);g=geometry(dots);cases[threshold].append(g)
            variants.append({'threshold':threshold,'dots':dots,'geometry':dict(zip(['t','K','residual_min','residual_max'],map(ratio,g)))})
        pages.append({'page':page,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop':list(box),'thresholds':variants})
    certificates=[]
    for threshold,(g1,g2) in cases.items():
        t1,k1,lo1,hi1=g1;t2,k2,lo2,hi2=g2
        lower=abs(k2-k1)-abs(t2-t1)*DIAGONAL_SQUARED
        upper=max(abs(lo2-hi1),abs(hi2-lo1))
        certificates.append({'threshold':threshold,'lower_bound':ratio(lower),'upper_bound':ratio(upper),
                             'margin':ratio(lower-upper),'incompatible':lower>upper})
    return {'pillow_version':PILLOW_VERSION,'coordinate_convention':'Zero-based integer pixel centers; page rectangle [0,2399] x [0,3599]',
            'maximum_radius_squared':DIAGONAL_SQUARED,'pages':pages,'certificates':certificates}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    d=measure()
    if args.check:assert d==json.loads(REPORT.read_bytes())
    else:REPORT.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8',newline='\n')
    for c in d['certificates']:print(c['threshold'],c['lower_bound']['decimal'],c['upper_bound']['decimal'],c['incompatible'])
