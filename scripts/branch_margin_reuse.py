"""Compare fixed decoded RGB margin windows on LP2-08 through LP2-14.

Requires Pillow. No alignment search, reflection, filtering, or resizing.
The windows were selected after inspecting the artwork, not preregistered.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
from PIL import Image, __version__ as pillow_version

ROOT=Path(__file__).resolve().parents[1]


def measure():
    rows=[];pixels={};groups=defaultdict(list)
    for page in range(8,15):
        name=f'lp2-{page:02}'
        path=ROOT/'images'/(name+'.jpg')
        x=0 if page%2==0 else 1850
        with Image.open(path) as source:
            assert source.size==(2400,3600)
            window=source.convert('RGB').crop((x,500,x+550,3000))
            data=window.tobytes()
        digest=hashlib.sha256(data).hexdigest()
        groups[digest].append(name);pixels[name]=data
        rows.append({'page':name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'rectangle_xywh':[x,500,550,2500],'rgb_sha256':digest})
    pairs=[]
    for left,right in itertools.combinations(pixels,2):
        a,b=pixels[left],pixels[right]
        equal=a==b
        pairs.append({'left':left,'right':right,'exact_rgb_bytes_equal':equal})
        assert equal==(next(r for r in rows if r['page']==left)['rgb_sha256']==next(r for r in rows if r['page']==right)['rgb_sha256'])
    return {'schema':'liberpedia-branch-margin-reuse-v1','pages':rows,
            'method':'Decode JPEG to RGB with Pillow; crop fixed [x,y,width,height] windows; compare every pair of byte streams directly. No resizing, reflection, alignment or thresholds.',
            'selection':'Exploratory windows selected after viewing the artwork. Margin windows include white background and do not assert complete isolation of every branch tip.',
            'equal_groups':list(groups.values()),'pairs':pairs,
            'limits':'Equality concerns only these decoded windows. Unequal windows are not proof of different original artwork. No cross-side transformation or cipher operation is established.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args()
    result=measure();path=ROOT/'exports/branch-margin-reuse.json'
    if a.write:path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    else:assert json.loads(path.read_bytes())==result
    print(f'PASS: 7 source images and 21 direct RGB comparisons; Pillow {pillow_version}')
    print(json.dumps(result['equal_groups']))
