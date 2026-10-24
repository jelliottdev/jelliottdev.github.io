"""Fresh count-only replay. Does not import or execute the glyph reader."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    p=json.loads((HERE/'plan.json').read_bytes())
    for item in p['inputs']:
        assert digest(ROOT/item['path'])==item['sha256'], 'Input hash mismatch: '+item['path']
    return p

def measure():
    plan=inputs() # all bytes verified before segmentation
    stored={r['id']:r for r in json.loads((HERE/'source/bands.json').read_bytes())}
    rows=[]
    for page in sorted({r['page'] for r in plan['boxes']}):
        bitmap=np.asarray(Image.open(ROOT/f'images/lp2-{page:02}.jpg').convert('L'))<128
        labels,total=ndimage.label(bitmap,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
        counts=np.bincount(labels.ravel())
        rects=[]
        for cid,s in enumerate(ndimage.find_objects(labels),1):
            if counts[cid]>=6: rects.append((s[1].start,s[0].start,s[1].stop,s[0].stop,int(counts[cid])))
        for box in [r for r in plan['boxes'] if r['page']==page]:
            chosen=[]
            for x0,y0,x1,y1,area in rects:
                ox=min(x1,box['x'][1])-max(x0,box['x'][0]); oy=min(y1,box['y'][1])-max(y0,box['y'][0])
                if ox>0 and oy>0 and 2*ox*oy >= (x1-x0)*(y1-y0): chosen.append([x0,y0,x1,y1,area])
            rows.append({'id':box['id'],'page':page,'n_reported':box['n'],'stored_n_components':stored[box['id']]['n_components'],'fresh_n_components':len(chosen),'components':chosen})
    rows.sort(key=lambda r:r['id'])
    return {'plan_sha256':digest(HERE/'plan.json'),'summary':{'bands':len(rows),'pages':len({r['page'] for r in rows}),'matches_stored':sum(r['fresh_n_components']==r['stored_n_components'] for r in rows),'matches_reported':sum(r['fresh_n_components']==r['n_reported'] for r in rows),'exceeds_16':sum(r['fresh_n_components']>16 for r in rows),'fresh_range':[min(r['fresh_n_components'] for r in rows),max(r['fresh_n_components'] for r in rows)]},'rows':rows}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    result=measure()
    if args.check: assert result==json.loads((HERE/'results.json').read_bytes())
    else: (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['summary'],sort_keys=True))
