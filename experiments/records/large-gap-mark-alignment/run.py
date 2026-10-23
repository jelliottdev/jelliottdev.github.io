"""Align source-guided punctuation/digit rows with the next clear image gap."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def measured(image,rect,threshold):
    x0,y0,x1,y1=rect
    crop=image.crop((x0,y0,x1,y1))
    pixels=crop.load()
    active=[y0+y for y in range(y1-y0) if sum(pixels[x,y]<threshold for x in range(x1-x0))>=5]
    boxes=[]
    for y in active:
        if not boxes or y-boxes[-1][1]>15: boxes.append([y,y])
        else: boxes[-1][1]=y
    return boxes,[b[0]-a[1]-1 for a,b in zip(boxes,boxes[1:])]

def marks(source, n):
    lines=source.splitlines()
    assert len(lines)>=n
    return [''.join(sorted(set(c for c in line if c.isascii() and (c.isdigit() or c in "'\"")))) for line in lines[:n]]

def report():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    rows=[]
    for item in plan['regions']:
        page=item['page']
        image_path=ROOT/'images'/f'{page}.jpg'
        record_path=ROOT/'data/pages'/f'{page}.json'
        record=json.loads(record_path.read_text(encoding='utf8'))
        image=Image.open(image_path).convert('L')
        assert image.size==(2400,3600)
        samples={}
        for threshold in (100,160,200):
            boxes,gaps=measured(image,item['xyxy'],threshold)
            assert len(boxes)==item['expected_lines']
            samples[str(threshold)]={'ink_row_boxes_inclusive':boxes,'blank_rows_after_line':gaps}
        raw=marks(record['raw'],item['expected_lines'])
        revised=marks(record.get('reviewed_text') or record['raw'],item['expected_lines'])
        aligned=[{'line':i+1,'raw_marker':raw[i],'reviewed_marker':revised[i],
                  'gap_after':samples['160']['blank_rows_after_line'][i]}
                 for i in range(item['expected_lines']-1)]
        rows.append({**item,'image_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
                     'page_record_sha256':hashlib.sha256(record_path.read_bytes()).hexdigest(),
                     'measurements':samples,'aligned':aligned})
    allrows=[x for page in rows for x in page['aligned']]
    wide=plan['descriptive_wide_gap_cutoff']
    review_marked=[x for x in allrows if x['reviewed_marker']]
    raw_marked=[x for x in allrows if x['raw_marker']]
    return {'regions':rows,'summary':{
        'measured_interline_gaps':len(allrows),
        'wide_gap_cutoff':wide,
        'reviewed_marked_lines':len(review_marked),
        'raw_marked_lines':len(raw_marked),
        'wide_gaps':sum(x['gap_after']>=wide for x in allrows),
        'reviewed_marked_and_wide':sum(x['gap_after']>=wide for x in review_marked),
        'raw_marked_and_wide':sum(x['gap_after']>=wide for x in raw_marked),
        'unmarked_and_wide_reviewed':sum(x['gap_after']>=wide and not x['reviewed_marker'] for x in allrows),
        'marked_and_not_wide_reviewed':sum(x['gap_after']<wide and bool(x['reviewed_marker']) for x in allrows),
        'marked_gap_range':[min(x['gap_after'] for x in review_marked),max(x['gap_after'] for x in review_marked)],
        'unmarked_gap_range':[min(x['gap_after'] for x in allrows if not x['reviewed_marker']),max(x['gap_after'] for x in allrows if not x['reviewed_marker'])]
    }}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    out=HERE/'results.json';payload=json.dumps(report(),ensure_ascii=False,indent=2)+'\n'
    if args.check:assert out.read_text(encoding='utf8')==payload
    else:out.write_text(payload,encoding='utf8')
    print(json.loads(payload)['summary'])

if __name__=='__main__':main()
