"""Measure ink-row gaps on four source-labeled LP2 pages."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def measure(image: Image.Image, rect: list[int], threshold: int) -> dict:
    x0, y0, x1, y1 = rect
    crop = image.crop((x0, y0, x1, y1))
    pix = crop.load()
    active = [y+y0 for y in range(y1-y0) if sum(pix[x,y] < threshold for x in range(x1-x0)) >= 5]
    assert active
    boxes = []
    start = end = active[0]
    for y in active[1:]:
        if y-end > 15:
            boxes.append([start,end])
            start = y
        end = y
    boxes.append([start,end])
    return {"ink_row_boxes_inclusive": boxes,
            "blank_rows_between": [b[0]-a[1]-1 for a,b in zip(boxes,boxes[1:])]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    rows = []
    for region in plan['regions']:
        path = ROOT/'images'/f"{region['page']}.jpg"
        image = Image.open(path).convert('L')
        assert image.size == (2400,3600)
        measurements = {str(t):measure(image,region['xyxy'],t) for t in plan['thresholds']}
        assert all(len(m['ink_row_boxes_inclusive']) == region['expected_lines'] for m in measurements.values())
        rows.append({**region,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'measurements':measurements})
    data = {"regions":rows,"gap_convention":"fully blank horizontal pixel rows; not baseline-to-baseline distance"}
    payload = json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    target = HERE/'results.json'
    if args.check:
        assert target.read_text(encoding='utf8') == payload
    else:
        target.write_text(payload,encoding='utf8')
    print({r['page']:r['measurements']['160']['blank_rows_between'] for r in rows})

if __name__ == '__main__':
    main()
