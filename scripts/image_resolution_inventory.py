"""Inventory dimensions and JFIF density of the 75 manuscript JPEGs.

Requires Pillow and original images in images/. Metadata is not evidence of
physical printing or scanning. --write saves; --check verifies the report.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'exports/image-resolution-inventory.json'


def report():
    rows=[]
    for release,count in [('lp1',17),('lp2',58)]:
        for n in range(count):
            page=f'{release}-{n:02}'
            path=ROOT/f'images/{page}.jpg'
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            record=json.loads((ROOT/f'data/pages/{page}.json').read_bytes())
            assert record['image_sha256']==digest,page
            with Image.open(path) as image:
                unit=image.info.get('jfif_unit')
                density=image.info.get('jfif_density')
                rows.append(dict(page=page,sha256=digest,bytes=path.stat().st_size,
                                 width=image.width,height=image.height,
                                 jfif_version=list(image.info.get('jfif_version',[])),
                                 jfif_unit=unit,jfif_density=list(density) if density else None,
                                 has_400_dpi_jfif=unit==1 and density==(400,400)))
    counts=Counter((x['width'],x['height']) for x in rows)
    return dict(page_count=len(rows),dimensions=[dict(width=w,height=h,pages=c) for (w,h),c in sorted(counts.items())],
                jfif_400_dpi_count=sum(x['has_400_dpi_jfif'] for x in rows),
                lp2_400_dpi_count=sum(x['has_400_dpi_jfif'] for x in rows if x['page'].startswith('lp2')),
                unit_meanings={'0':'No physical unit; density is an aspect ratio.','1':'Pixels per inch.','2':'Pixels per centimetre.'},
                rows=rows,limits=['This inventory covers manuscript originals LP1-00–16 and LP2-00–57 only.',
                                 'JFIF density is file metadata, not proof of print size, scanning or creation software.',
                                 'Equal dimensions do not guarantee corresponding artwork is aligned.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args();result=report()
    if args.write:
        OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    elif args.check:
        assert json.loads(OUTPUT.read_bytes())==result
        print('PASS: 75 original JPEG hashes, dimensions and JFIF fields match the inventory.')
    else:
        print(json.dumps(result,indent=2))
