"""Image-only row proposals and coverage against the frozen visual reference.

This does not recognize glyphs or certify transcription accuracy.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, __version__ as PILLOW_VERSION

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'experiments/records/image-row-coverage/visual-reference.json'
REFERENCE_SHA='d09db33d464fb2149a77a71bc616e645ed7bd16d85f68ed4111963023ebb229e'
PLAN=ROOT/'experiments/plans/image-row-coverage.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def detect(path):
    with Image.open(path) as original:
        im=original.convert('L')
    w,h=im.size;x0=int(w*.22);x1=int(w*.78)
    counts=[sum(im.crop((x0,y,x1,y+1)).histogram()[:128]) for y in range(h)]
    active=[100*c>x1-x0 for c in counts]
    bands=[];start=None
    for y,on in enumerate(active+[False]):
        if on and start is None:start=y
        if not on and start is not None:
            if y-start>=20:bands.append([start,y])
            start=None
    merged=[]
    for a,b in bands:
        if merged and a-merged[-1][1]<12:merged[-1][1]=b
        else:merged.append([a,b])
    return {'column':[x0,x1],'dark_pixel_counts':counts,'unmerged_bands':bands,'bands':merged}


def overlaps(a,b):
    intersection=max(0,min(a[1],b[1])-max(a[0],b[0]))
    union=max(a[1],b[1])-min(a[0],b[0])
    return intersection>0 and 2*intersection>=union


def maximum(edges,skip_row=None,skip_band=None):
    assigned={}
    def augment(row,seen):
        for band in edges[row]:
            if band==skip_band or band in seen:continue
            seen.add(band)
            if band not in assigned or augment(assigned[band],seen):
                assigned[band]=row;return True
        return False
    for row in range(len(edges)):
        if row!=skip_row:augment(row,set())
    return len(assigned)


def coverage(rows,bands):
    edges=[[j for j,b in enumerate(bands) if overlaps(r['y'],b)] for r in rows]
    size=maximum(edges)
    possible=[[j for j in edge if 1+maximum(edges,i,j)==size] for i,edge in enumerate(edges)]
    guaranteed=[maximum(edges,i)<size for i in range(len(rows))]
    used={j for edge in possible for j in edge}
    return {'maximum_matched_rows':size,'eligible_edges':edges,'possible_bands_in_maximum_matchings':possible,
            'row_matched_in_every_maximum_matching':guaranteed,
            'bands_in_no_maximum_matching':[j for j in range(len(bands)) if j not in used]}


def run():
    assert sha(REFERENCE)==REFERENCE_SHA
    reference=json.loads(REFERENCE.read_bytes());plan=json.loads(PLAN.read_bytes())
    assert reference['plan_sha256']==sha(PLAN)
    assert reference['protocol_sha256']==plan['protocol_sha256']==sha(ROOT/plan['protocol'])
    pages=[]
    for page in reference['pages']:
        source=ROOT/page['image']['path'];assert sha(source)==page['image']['sha256']
        detected=detect(source)
        runic=[r for r in page['rows'] if r['kind']=='runic']
        others=[r for r in page['rows'] if r['kind']!='runic']
        matched=coverage(runic,detected['bands'])
        controls=[{'omitted_runic_row':i,'y':r['y'],
                   'image_only_possible_bands':matched['possible_bands_in_maximum_matchings'][i],
                   'image_only_guaranteed_match':matched['row_matched_in_every_maximum_matching'][i],
                   'candidate_inventory_only_visits_omitted_row':False}
                  for i,r in enumerate(runic)]
        pages.append({'page':page['page'],'image_sha256':sha(source),'runic_rows':runic,
                      'other_text_rows':others,**detected,**matched,'omission_controls':controls,
                      'other_row_matches':[[j for j,b in enumerate(detected['bands']) if overlaps(r['y'],b)] for r in others]})
    return {'status':'computed; independent implementation and overlay review required',
            'reference_sha256':sha(REFERENCE),'plan_sha256':sha(PLAN),'script_sha256':sha(Path(__file__)),
            'pillow_version':PILLOW_VERSION,'pages':pages,
            'limits':'Fixed eight-page convenience sample and manual approximate body intervals. No rune recognition, actual omission finding, all-page certification or independent-trial accuracy. Candidate-only arm is a coverage restriction by construction.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new output file')
    result=run()
    with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    for page in result['pages']:
        print(page['page'],len(page['bands']),'bands;',page['maximum_matched_rows'],'of',len(page['runic_rows']),'reference rune rows matched')
