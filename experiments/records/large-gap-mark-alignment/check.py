"""Independent flat-pixel and text-line check of the six fixed regions."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
saved=json.loads((HERE/'results.json').read_text(encoding='utf8'))
allrows=[]
for region, result in zip(plan['regions'],saved['regions']):
    page=region['page'];assert page==result['page']
    record=json.loads((ROOT/'data/pages'/f'{page}.json').read_text(encoding='utf8'))
    assert record['raw']==(ROOT/'text'/f'{page}.txt').read_text(encoding='utf8')
    lines=(record.get('reviewed_text') or record['raw']).splitlines()
    x0,y0,x1,y1=region['xyxy'];w=x1-x0
    flat=list(Image.open(ROOT/'images'/f'{page}.jpg').convert('L').crop((x0,y0,x1,y1)).getdata())
    for threshold in (100,160,200):
        active=[]
        for y in range(y1-y0):
            band=flat[y*w:(y+1)*w]
            if sum(1 for pixel in band if pixel<threshold)>=5:active.append(y0+y)
        intervals=[]
        for y in active:
            if not intervals or y-intervals[-1][1]>15:intervals.append([y,y])
            else:intervals[-1][1]=y
        assert intervals==result['measurements'][str(threshold)]['ink_row_boxes_inclusive']
        assert [b[0]-a[1]-1 for a,b in zip(intervals,intervals[1:])]==result['measurements'][str(threshold)]['blank_rows_after_line']
    for i,row in enumerate(result['aligned']):
        marks={c for c in lines[i] if c.isascii() and (c.isdigit() or c in "'\"")}
        assert ''.join(sorted(marks))==row['reviewed_marker']
        allrows.append(row)
assert len(allrows)==34
marked=[r for r in allrows if r['reviewed_marker']]
assert len(marked)==6
assert sorted(r['gap_after'] for r in marked)==[108,109,110,110,110,110]
assert max(r['gap_after'] for r in allrows if not r['reviewed_marker'])==75
print('Independent page-text and flat-pixel checks reproduce all six marked gaps and 28 controls.')
