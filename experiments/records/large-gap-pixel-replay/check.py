"""Independent row-mask reduction over the fixed original-image rectangles."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
results=json.loads((HERE/'results.json').read_text(encoding='utf8'))
for region, result in zip(plan['regions'],results['regions']):
    assert region['page']==result['page']
    x0,y0,x1,y1=region['xyxy']
    crop=Image.open(ROOT/'images'/f"{region['page']}.jpg").convert('L').crop((x0,y0,x1,y1))
    width=x1-x0
    values=list(crop.getdata())
    for threshold in plan['thresholds']:
        active=[]
        for local_y in range(y1-y0):
            line=values[local_y*width:(local_y+1)*width]
            if len([x for x in line if x<threshold])>=5:
                active.append(local_y+y0)
        runs=[]
        for y in active:
            if not runs or y-runs[-1][1]>15:
                runs.append([y,y])
            else:
                runs[-1][1]=y
        saved=result['measurements'][str(threshold)]
        assert runs==saved['ink_row_boxes_inclusive'],(region['page'],threshold)
        assert [b[0]-a[1]-1 for a,b in zip(runs,runs[1:])]==saved['blank_rows_between']
print('Independent flat-pixel projection matches all four regions at all three thresholds.')
