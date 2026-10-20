"""Compare fixed side-dot rectangles across LP2-40–55. Requires Pillow.

Download the 16 original JPEGs into images/ before running this script.
Coordinates are original pixels, left/top included, right/bottom excluded.
No alignment, rescaling, reflection or thresholding is applied.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/side-dot-reuse.json'
BOXES = {'left':[340,1450,450,1570], 'right':[1950,1450,2060,1570]}


def report():
    rows, baseline = [], {}
    for n in range(40,56):
        page = f'lp2-{n:02}'
        path = ROOT / f'images/{page}.jpg'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        record = json.loads((ROOT / f'data/pages/{page}.json').read_bytes())
        assert digest == record['image_sha256'], f'Image differs: {page}'
        with Image.open(path) as image:
            assert image.size == (2400,3600)
            decoded = image.convert('RGB')
            regions = {}
            for side, box in BOXES.items():
                rgb = decoded.crop(box)
                values = list(rgb.getdata())
                gray = list(rgb.convert('L').getdata())
                baseline.setdefault(side, (values,gray))
                unequal = sum(a!=b for a,b in zip(values,baseline[side][0]))
                gray_unequal = sum(a!=b for a,b in zip(gray,baseline[side][1]))
                assert unequal == gray_unequal == 0, (page,side,unequal,gray_unequal)
                regions[side] = dict(rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
                                     unequal_rgb_pixels=unequal, unequal_grayscale_pixels=gray_unequal)
        rows.append(dict(page=page, image_sha256=digest, regions=regions))
    return dict(baseline='lp2-40', boxes=BOXES, pixels_per_region=13200,
                coordinate_convention='Zero-based original pixels; right and bottom exclusive.',
                rows=rows, all_16_pages_identical_in_each_region=True,
                scope='Each side compared with the same side on LP2-40; not left versus right.',
                limits=['Only these rectangles are compared, not complete borders or pages.',
                        'Pixel equality supports artwork reuse, not a cipher operation or proof of decoration.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report()
    if args.write:
        OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    elif args.check:
        assert json.loads(OUTPUT.read_bytes()) == result, 'Saved report differs'
        print(f'PASS: both regions match on all 16 pages (Pillow {pillow_version}).')
    else:
        print(json.dumps(result,indent=2))
