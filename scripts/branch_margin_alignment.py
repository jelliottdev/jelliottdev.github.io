"""Bounded exploratory branch alignment; Pillow and NumPy. --write or --check.

Original JPEGs are never changed. The output image is a measurement overlay.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
PAGES=['lp2-09','lp2-10','lp2-11','lp2-12','lp2-13','lp2-14']


def measure():
    inputs=[];windows={}
    for page in PAGES:
        path=ROOT/f'images/{page}.jpg';raw=path.read_bytes()
        inputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()})
        im=Image.open(io.BytesIO(raw)).convert('L');assert im.size==(2400,3600)
        x=1800 if int(page[-2:])%2 else 0
        windows[page]=np.asarray(im.crop((x,600,x+550,2950)))
    a=windows['lp2-09']<128;b=windows['lp2-10']<128
    ys,xs=np.where(a);nb=int(b.sum());search=[]
    for orientation in ['same','horizontal','vertical','both']:
        xx=549-xs if orientation in ['horizontal','both'] else xs
        yy=2349-ys if orientation in ['vertical','both'] else ys
        best=None
        for dy in range(-8,9):
            for dx in range(-100,101):
                tx=xx+dx;ty=yy+dy;ok=(tx>=0)&(tx<550)&(ty>=0)&(ty<2350)
                intersection=int(b[ty[ok],tx[ok]].sum())
                # Retain first maximum in dy,dx order; no score-dependent tie rule.
                if best is None or intersection>best['intersection']:
                    best={'dx':dx,'dy':dy,'intersection':intersection,'dice':2*intersection/(len(xs)+nb)}
        search.append({'orientation':orientation,**best})
    selected=next(x for x in search if x['orientation']=='same')
    assert (selected['dx'],selected['dy'])==(16,0)
    checks=[]
    for right in ['lp2-09','lp2-11','lp2-13']:
        for left in ['lp2-10','lp2-12','lp2-14']:
            for threshold in [64,128,192]:
                source=windows[right]<threshold;target=windows[left]<threshold
                sy,sx=np.where(source)
                assert np.all(sx+16<550) # no foreground clipped by this translation
                shifted=np.zeros_like(source);shifted[sy,sx+16]=True
                inter=int((shifted&target).sum());na=int(source.sum());nb=int(target.sum())
                # Independent Pillow logical intersection, same integer shift.
                mask=Image.fromarray(np.uint8(source)*255).convert('1')
                canvas=Image.new('1',mask.size);canvas.paste(mask,(16,0))
                other=Image.fromarray(np.uint8(target)*255).convert('1')
                assert sum(ImageChops.logical_and(canvas,other).getdata())//255==inter
                checks.append({'right':right,'left':left,'threshold':threshold,'source_dark':na,'target_dark':nb,'intersection':inter,'dice':2*inter/(na+nb)})
    shifted=np.zeros_like(a);shifted[:,16:]=a[:,:-16]
    overlay=np.full((*a.shape,3),255,dtype=np.uint8)
    overlay[shifted&b]=[38,59,69];overlay[shifted&~b]=[49,95,115];overlay[b&~shifted]=[171,112,42]
    stream=io.BytesIO();Image.fromarray(overlay).save(stream,format='PNG')
    report={'inputs':inputs,'method':'Pillow L conversion; pixel<threshold. Right crop [1800,600,550,2350], left [0,600,550,2350]. Exploratory crop/translation bounds chosen after viewing originals, not a preregistered significance test.',
            'search':{'pair':['lp2-09','lp2-10'],'threshold':128,'dx_range_inclusive':[-100,100],'dy_range_inclusive':[-8,8],'candidates_per_orientation':3417,'results':search},
            'selected_transform':'Same orientation; add16 to right-crop x to map into left-crop coordinates. In full-page coordinates x_left=x_right-1784 and y_left=y_right.',
            'fixed_transform_checks':checks,
            'limitations':'Dark-mask overlap, not identical RGB bytes, exact source-image provenance or a reconstructed processing pipeline. No scaling, rotation beyond the four listed orientations, or warping searched. No inference about reversing text or cipher meaning. Similar pages are not independent evidence samples.'}
    return report,stream.getvalue()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args()
    report,png=measure();outputs={'exports/branch-margin-alignment.json':(json.dumps(report,indent=2)+'\n').encode(),'exports/figures/branch-alignment-overlay.png':png}
    for name,raw in outputs.items():
        if args.check:assert (ROOT/name).read_bytes()==raw,name
        elif args.write:(ROOT/name).write_bytes(raw)
    print(json.dumps(report['search'],indent=2))
