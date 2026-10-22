"""Fixed-region original-JPEG line-gap audit; not a binary decoder."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(page, box, cutoff):
    x0, y0, x1, y1 = box
    image = Image.open(ROOT / 'images' / f'{page}.jpg').convert('L')
    if image.size != (2400, 3600):
        raise ValueError(f'{page}: unexpected dimensions {image.size}')
    crop = image.crop(box)
    pixels = crop.load()
    active = []
    for y in range(y1-y0):
        count = sum(pixels[x, y] < cutoff for x in range(x1-x0))
        if count >= 5:
            active.append(y0+y)
    if not active:
        raise ValueError('empty region')
    groups = []
    start = last = active[0]
    for y in active[1:]:
        if y-last > 15:
            groups.append([start, last])
            start = y
        last = y
    groups.append([start, last])
    return {'line_boxes_y_inclusive': groups,
            'blank_rows_between_lines': [b[0]-a[1]-1 for a,b in zip(groups, groups[1:])],
            'line_starts_y': [b[0] for b in groups]}


def compute():
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    for entry in plan['inputs']:
        if sha(ROOT / entry['path']) != entry['sha256']:
            raise ValueError(f"image SHA-256 mismatch: {entry['path']}")
    regions = []
    for region in plan['regions']:
        samples = {str(cutoff): measure(region['page'], region['rectangle_xyxy'], cutoff)
                   for cutoff in (100, 160, 200)}
        for cutoff, sample in samples.items():
            if len(sample['line_boxes_y_inclusive']) != region['expected_rows']:
                raise ValueError(f"{region['id']}: {len(sample['line_boxes_y_inclusive'])} rows at {cutoff}")
        regions.append({**region, 'measurements': samples})
    return {'plan_sha256': sha(plan_path), 'regions': regions,
            'interpretation': 'A measured interline anomaly is not a decoded bit. Numeric and rune regions differ in typeface and page function; the supplied word-gap screenshots and a controlled font-rendering source are unavailable.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = compute()
    path = HERE / 'results.json'
    if args.check:
        if result != json.loads(path.read_text(encoding='utf-8')):
            raise SystemExit('results.json does not reproduce')
        print('PASS: fixed-coordinate line boxes and threshold checks reproduce')
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(path)


if __name__ == '__main__':
    main()
