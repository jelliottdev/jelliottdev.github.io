"""Independent scalar-pixel, regex-band and exhaustive-matching reconstruction."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from PIL import Image, __version__ as PILLOW_VERSION

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def matchable(a,b):
    shared=max(0,min(a[1],b[1])-max(a[0],b[0]))
    union=(a[1]-a[0])+(b[1]-b[0])-shared
    return Fraction(shared,union)>=Fraction(1,2)


def all_best(edges):
    best=-1;solutions=[]
    def visit(i,used,pairs):
        nonlocal best,solutions
        if i==len(edges):
            if len(pairs)>best:best=len(pairs);solutions=[]
            if len(pairs)==best:solutions.append(set(pairs))
            return
        visit(i+1,used,pairs)
        for band in edges[i]:
            if band not in used:visit(i+1,used|{band},pairs+[(i,band)])
    visit(0,set(),[])
    return best,solutions


def check(report_path):
    report=json.loads(report_path.read_bytes())
    ref_path=ROOT/'experiments/records/image-row-coverage/visual-reference.json'
    plan_path=ROOT/'experiments/plans/image-row-coverage.json'
    reference=json.loads(ref_path.read_bytes());plan=json.loads(plan_path.read_bytes())
    assert sha(ref_path)==report['reference_sha256']=='d09db33d464fb2149a77a71bc616e645ed7bd16d85f68ed4111963023ebb229e'
    assert sha(plan_path)==reference['plan_sha256']==report['plan_sha256']
    assert sha(ROOT/plan['protocol'])==plan['protocol_sha256']==reference['protocol_sha256']
    assert report['script_sha256']==sha(ROOT/'scripts/image_row_coverage.py')
    assert len(report['pages'])==len(reference['pages'])==len(plan['inputs'])==8
    total_rows=0;total_bands=0;total_matches=0
    for page,ref,input_spec in zip(report['pages'],reference['pages'],plan['inputs']):
        assert page['page']==ref['page'] and ref['image']==input_spec
        source=ROOT/input_spec['path']
        assert sha(source)==input_spec['sha256']==page['image_sha256']
        with Image.open(source) as original:
            assert list(original.size)==ref['dimensions']
            im=original.convert('L')
        w,h=im.size;x0=w*22//100;x1=w*78//100;pixels=im.tobytes()
        counts=[sum(v<128 for v in pixels[y*w+x0:y*w+x1]) for y in range(h)]
        assert counts==page['dark_pixel_counts'] and page['column']==[x0,x1]
        active=''.join('1' if Fraction(c,x1-x0)>Fraction(1,100) else '0' for c in counts)
        spans=[list(m.span()) for m in re.finditer('1{20,}',active)]
        assert spans==page['unmerged_bands']
        groups=[]
        for span in spans:
            if groups and span[0]-groups[-1][-1][1]<12:groups[-1].append(span)
            else:groups.append([span])
        bands=[[g[0][0],g[-1][1]] for g in groups]
        assert bands==page['bands']
        rows=[r for r in ref['rows'] if r['kind']=='runic']
        others=[r for r in ref['rows'] if r['kind']!='runic']
        assert rows==page['runic_rows'] and others==page['other_text_rows']
        edges=[[j for j,b in enumerate(bands) if matchable(r['y'],b)] for r in rows]
        best,choices=all_best(edges)
        possible=[[j for j in edge if any((i,j) in choice for choice in choices)] for i,edge in enumerate(edges)]
        guaranteed=[all(any(a==i for a,_ in c) for c in choices) for i in range(len(rows))]
        assert edges==page['eligible_edges'] and best==page['maximum_matched_rows']
        assert possible==page['possible_bands_in_maximum_matchings']
        assert guaranteed==page['row_matched_in_every_maximum_matching']
        used={b for choice in choices for _,b in choice}
        assert [j for j in range(len(bands)) if j not in used]==page['bands_in_no_maximum_matching']
        assert [[j for j,b in enumerate(bands) if matchable(r['y'],b)] for r in others]==page['other_row_matches']
        expected=[{'omitted_runic_row':i,'y':r['y'],'image_only_possible_bands':possible[i],
                   'image_only_guaranteed_match':guaranteed[i],'candidate_inventory_only_visits_omitted_row':False}
                  for i,r in enumerate(rows)]
        assert expected==page['omission_controls']
        total_rows+=len(rows);total_bands+=len(bands);total_matches+=best
    return {'report_sha256':sha(report_path),'reference_sha256':sha(ref_path),'plan_sha256':sha(plan_path),
            'checker_sha256':sha(Path(__file__)),'checker_pillow_version':PILLOW_VERSION,
            'producer_pillow_version':report['pillow_version'],'pages_checked':8,
            'runic_reference_rows':total_rows,'proposed_bands':total_bands,'maximum_matches_total':total_matches,
            'omission_controls_checked':total_rows,
            'method':'Scalar grayscale-byte thresholds, regex active runs, separately grouped intervals, rational IoU and exhaustive enumeration of all maximum matchings. Shares Pillow image decoding, not the producer implementation.',
            'limits':'Computational agreement with the frozen visual inventory; does not validate manual annotations or replace overlay review.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    if args.receipt.exists():parser.error('Choose a new receipt path')
    result=check(args.report)
    args.receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))
