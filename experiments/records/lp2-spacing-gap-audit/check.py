"""Independent byte-projection check of the fixed LP2 line-gap sample."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def independent_rows(page, rect):
    x0,y0,x1,y1 = rect
    image = Image.open(ROOT/'images'/f'{page}.jpg').convert('L')
    row_bytes = image.crop(rect).tobytes()
    stride = x1-x0
    marked = []
    for i in range(y1-y0):
        row = row_bytes[i*stride:(i+1)*stride]
        if sum(value<160 for value in row) >= 5:
            marked.append(y0+i)
    bands = []
    for y in marked:
        if not bands or y-bands[-1][-1] > 15:
            bands.append([y])
        else:
            bands[-1].append(y)
    return [[band[0],band[-1]] for band in bands]


def main():
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    expected={'lp2-15-panel':[62,61,79],
              'lp2-15-runes':[74]*6,
              'lp2-14-runes':[74,75,74,74,74,73],
              'lp2-16-runes':[74,75,74,74,74,73,73,74,73,73,74]}
    assert {r['id'] for r in data['regions']} == set(expected)
    for r in data['regions']:
        bands=independent_rows(r['page'],r['rectangle_xyxy'])
        saved=r['measurements']['160']
        gaps=[b[0]-a[1]-1 for a,b in zip(bands,bands[1:])]
        assert bands==saved['line_boxes_y_inclusive'],r['id']
        assert gaps==saved['blank_rows_between_lines']==expected[r['id']],r['id']
        assert all(0 < gap < 100 for gap in gaps)
    assert expected['lp2-15-panel'][2]-max(expected['lp2-15-panel'][:2])==17
    print('PASS: independent projection matches all line boxes; final panel gap exceeds earlier panel gaps by at least 17 px')


if __name__=='__main__':
    main()
