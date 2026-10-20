"""Measure and compare the five-dot groups on LP2-07, 23 and 56.

Requires Pillow, original JPEGs, and bundled measure_region.py. No cipher test.
All 120 correspondences are tried for each of four fixed axis operations.
Positive uniform scale and translation are fitted; no free angle or shear.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from PIL import Image
from measure_region import component_records
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'exports/five-dot-geometry.json'
REGIONS={'lp2-07':[550,2700,1200,600],'lp2-23':[500,300,1300,650],'lp2-56':[500,2320,1250,500]}
OPERATIONS={'identity':(1,1),'top-bottom reflection':(1,-1),'left-right reflection':(-1,1),'half-turn':(-1,-1)}


def fit(source,target,signs,permutation):
    a=[(x*signs[0],y*signs[1]) for x,y in source]
    b=[target[i] for i in permutation]
    am=[sum(p[k] for p in a)/len(a) for k in (0,1)]
    bm=[sum(p[k] for p in b)/len(b) for k in (0,1)]
    denominator=sum((p[k]-am[k])**2 for p in a for k in (0,1))
    scale=sum((p[k]-am[k])*(q[k]-bm[k]) for p,q in zip(a,b) for k in (0,1))/denominator
    if scale<=0:return None
    shift=[bm[k]-scale*am[k] for k in (0,1)]
    errors=[math.dist([scale*p[k]+shift[k] for k in (0,1)],q) for p,q in zip(a,b)]
    distances=[abs(math.dist(b[i],b[j])-scale*math.dist(a[i],a[j])) for i,j in itertools.combinations(range(5),2)]
    return dict(scale=scale,translation=shift,source_to_target_indices=list(permutation),
                rms_pixels=math.sqrt(sum(e*e for e in errors)/5),maximum_pixels=max(errors),
                maximum_pair_distance_residual=max(distances))


def compare(source,target):
    ranked=[]
    for operation,signs in OPERATIONS.items():
        fits=[fit(source,target,signs,p) for p in itertools.permutations(range(5))]
        valid=[x for x in fits if x is not None]
        if valid:
            best=min(valid,key=lambda x:x['rms_pixels'])
            ranked.append(dict(operation=operation,axis_signs=list(signs),positive_scale_trials=len(valid),**best))
    return sorted(ranked,key=lambda x:x['rms_pixels'])


def measure(page,threshold):
    x,y,w,h=REGIONS[page]
    with Image.open(ROOT/f'images/{page}.jpg') as image:
        gray=image.convert('L').crop((x,y,x+w,y+h))
        points={(x+i%w,y+i//w) for i,v in enumerate(gray.getdata()) if v<threshold}
    components,_=component_records(points,8,1000)
    components.sort(key=lambda p:p['centroid'][0])
    assert len(components)==5,(page,threshold,len(components))
    return components


def controls():
    points=[(0,0),(8,1),(2,5),(7,9),(11,3)]
    for name,signs in OPERATIONS.items():
        transformed=[(2*x*signs[0]+37,2*y*signs[1]-15) for x,y in points]
        winner=compare(points,transformed)[0]
        assert winner['operation']==name and winner['rms_pixels']<1e-10
    assert compare(points,[(2*x,3*y) for x,y in points])[0]['rms_pixels']>0.1


def report():
    controls()
    regions=[];measured={}
    for page,rect in REGIONS.items():
        image=ROOT/f'images/{page}.jpg'
        digest=hashlib.sha256(image.read_bytes()).hexdigest()
        assert digest==json.loads((ROOT/f'data/pages/{page}.json').read_bytes())['image_sha256']
        thresholds={t:measure(page,t) for t in (120,140,160,180)}
        measured[page]=thresholds
        regions.append(dict(page=page,rect=rect,image_sha256=digest,components=thresholds[140],
                            threshold_maximum_centroid_change={str(t):max(math.dist(a['centroid'],b['centroid']) for a,b in zip(thresholds[140],thresholds[t])) for t in (120,160,180)}))
    pairs=[]
    for source,target in itertools.combinations(REGIONS,2):
        results={t:compare([x['centroid'] for x in measured[source][t]],[x['centroid'] for x in measured[target][t]]) for t in (120,140,160,180)}
        pairs.append(dict(source=source,target=target,ranked_operations=results[140],
                          threshold_winners={str(t):results[t][0] for t in (120,160,180)}))
    return dict(rect_convention='Original-image x,y,width,height; no resizing.',
                selection='Grayscale strictly below 140; eight-connected components of at least 1000 pixels; centroids rounded to six decimals; labels sorted left to right.',
                trials_per_pair_per_threshold=480,thresholds=[120,140,160,180],regions=regions,pairs=pairs,
                controls='Four synthetic axis operations recovered; anisotropic scaling fails exact-fit control.',
                limits=['Selected component centroids, not whole-raster equality.',
                        'Only four axis operations with positive uniform scale and translation; no arbitrary rotations or shear.',
                        'Residuals measure geometric agreement, not chance probability or a cipher instruction.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args();result=report()
    if args.write:OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    elif args.check:
        assert json.loads(OUTPUT.read_bytes())==result
        print('PASS: original image hashes, 60 component measurements, all correspondence fits, controls and report.')
    else:print(json.dumps(result,indent=2))
