"""Export checked original-pixel line gaps and self-contained image overlays.

The two experiment directories are read-only evidence. Legacy Pillow rectangles
were half-open; exported rectangles and ink/gap endpoints are inclusive.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import statistics

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = (100, 160, 200)
LABELS = {
    'lp2-04': 'LP2-04 body text', 'lp2-35': 'LP2-35 body text',
    'lp2-57': 'LP2-57 parable text', 'lp2-14': 'LP2-14 ordinary rune spacing',
    'lp2-15-panel': 'LP2-15 number panel', 'lp2-15-runes': 'LP2-15 lower rune text',
    'lp2-16': 'LP2-16 ordinary rune spacing',
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(gray: np.ndarray, rect: list[int], threshold: int) -> dict:
    x0, y0, x1, y1 = rect
    counts = np.count_nonzero(gray[y0:y1+1, x0:x1+1] < threshold, axis=1)
    active = np.flatnonzero(counts >= 5) + y0
    if not len(active):
        raise ValueError('No detected ink rows')
    groups = np.split(active, np.flatnonzero(np.diff(active) > 15) + 1)
    lines = [{'top': int(group[0]), 'bottom': int(group[-1])} for group in groups]
    gaps = [{'from_line': i+1, 'to_line': i+2, 'top': a['bottom']+1,
             'bottom': b['top']-1, 'pixels': b['top']-a['bottom']-1}
            for i, (a, b) in enumerate(zip(lines, lines[1:]))]
    return {'lines': lines, 'gaps': gaps}


def checked_regions(root: Path) -> list[dict]:
    regions = []
    seen = {}
    for record in ('large-gap-pixel-replay', 'lp2-spacing-gap-audit'):
        folder = root / 'experiments/records' / record
        result = json.loads((folder/'results.json').read_text(encoding='utf8'))
        plan = json.loads((folder/'plan.json').read_text(encoding='utf8'))
        hashes = {p['path']: p['sha256'] for p in plan.get('inputs', [])}
        for source in result['regions']:
            page = source['page']
            legacy = source.get('xyxy', source.get('rectangle_xyxy'))
            signature = (page, tuple(legacy))
            expected = {}
            for threshold in THRESHOLDS:
                value = source['measurements'][str(threshold)]
                expected[str(threshold)] = {
                    'boxes': value.get('ink_row_boxes_inclusive', value.get('line_boxes_y_inclusive')),
                    'gaps': value.get('blank_rows_between', value.get('blank_rows_between_lines')),
                }
            if signature in seen:
                existing = seen[signature]
                if existing['expected'] != expected:
                    raise ValueError('Duplicated source region disagrees')
                existing['source_records'].append(record)
                continue
            identifier = source.get('id', page)
            identifier = {'lp2-14-runes': 'lp2-14', 'lp2-16-runes': 'lp2-16'}.get(identifier, identifier)
            entry = {'id': identifier, 'page': page, 'legacy_rect': legacy,
                     'expected': expected, 'source_records': [record],
                     'image_sha256': source.get('image_sha256', hashes.get(f'images/{page}.jpg'))}
            regions.append(entry)
            seen[signature] = entry
    return regions


def build(root: Path = ROOT) -> dict:
    rows = []
    for source in checked_regions(root):
        path = root / 'images' / f"{source['page']}.jpg"
        if digest(path) != source['image_sha256']:
            raise ValueError(f'Original image changed: {path}')
        image = Image.open(path).convert('L')
        if image.size != (2400, 3600):
            raise ValueError('Unexpected original image dimensions')
        gray = np.asarray(image)
        x0, y0, x1, y1 = source['legacy_rect']
        rect = [x0, y0, x1-1, y1-1]
        adjustment = None
        if source['id'] == 'lp2-35':
            adjustment = {'source_rect_xyxy': list(rect), 'new_bottom_inclusive': 2950,
                          'reason': 'The historical crop clipped the final text line at 2799. Extend only the lower edge to include its complete ink band; all shared gaps must remain identical.'}
            rect[3] = 2950
        measurements = {str(t): measure(gray, rect, t) for t in THRESHOLDS}
        for threshold, actual in measurements.items():
            expected = source['expected'][threshold]
            boxes = [[line['top'], line['bottom']] for line in actual['lines']]
            gaps = [gap['pixels'] for gap in actual['gaps']]
            if adjustment:
                if boxes[:-1] != expected['boxes'][:-1] or boxes[-1][0] != expected['boxes'][-1][0]:
                    raise ValueError('LP2-35 extension changed shared line endpoints')
                if not expected['boxes'][-1][1] < boxes[-1][1] < rect[3]:
                    raise ValueError('LP2-35 complete final ink edge not observed')
            elif boxes != expected['boxes']:
                raise ValueError(f"{source['id']}: source line endpoints differ at{threshold}")
            if gaps != expected['gaps']:
                raise ValueError(f"{source['id']}: source gap counts differ at{threshold}")
        primary = measurements['160']
        row = {'id': source['id'], 'page': source['page'], 'label': LABELS[source['id']],
               'rect_xyxy': rect, 'image_path': f"images/{source['page']}.jpg",
               'image_sha256': source['image_sha256'], 'width': 2400, 'height': 3600,
               'lines': primary['lines'], 'gaps': primary['gaps'], 'measurements': measurements,
               'source_records': source['source_records'],
               'overlay_path': f"exports/line-gaps/{source['id']}.svg", 'notes': []}
        if adjustment:
            row['region_adjustment'] = adjustment
            row['notes'].append('New lower boundary includes the complete last line. All 11 gap widths match the historical clipped crop at every cutoff.')
        if source['id'] == 'lp2-15-runes':
            row['notes'].append('Red margin and number panel excluded from this lower-text region.')
        rows.append(row)
    pages = sorted({row['page'] for row in rows})
    return {'schema': 'liberpedia-line-gap-measurements-v1',
            'coverage': {'pages': pages, 'page_count': len(pages), 'region_count': len(rows),
                         'complete_census': False,
                         'note': 'Seven checked regions on six pages; LP2-14 is deduplicated. This is not a census of every reported wide-gap page.'},
            'method': {'default_threshold': 160, 'thresholds': list(THRESHOLDS),
                       'minimum_dark_pixels': 5, 'split_active_row_distance': 15,
                       'coordinate_convention': 'inclusive original pixels',
                       'line_references': 'one-based within region',
                       'note': 'A row is ink-active when at least 5 pixels in the measured strip are below the grayscale cutoff. Successive active rows more than 15 pixels apart start another band. Gap width counts intervening inactive rows, not baseline distance or pure-white full-page rows.'},
            'rows': rows}


def overlay(root: Path, row: dict) -> str:
    image = Image.open(root/row['image_path']).convert('RGB')
    gaps = row['gaps']
    longest = max(gaps, key=lambda g: g['pixels'])
    middle = statistics.median(g['pixels'] for g in gaps)
    ordinary = min((g for g in gaps if g is not longest),
                   key=lambda g: (abs(g['pixels']-middle), g['from_line']))
    elements = []
    y = 110.
    x0, _, x1, _ = row['rect_xyxy']
    scale = 420/(x1-x0+1)
    for title, gap in [('Longest gap', longest), ('Typical gap', ordinary)]:
        previous = row['lines'][gap['from_line']-1]
        following = row['lines'][gap['to_line']-1]
        crop_top = previous['top']-10
        crop_bottom = following['bottom']+10
        crop = image.crop((x0, crop_top, x1+1, crop_bottom+1))
        buffer = io.BytesIO()
        crop.save(buffer, format='PNG')  # Native dimensions, lossless decoded JPEG pixels.
        encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
        height = crop.height*scale
        elements.append(f'<text x="16" y="{y:.2f}" font-size="28">{title} · lines {gap["from_line"]}–{gap["to_line"]}</text>')
        image_y = y+20
        elements.append(f'<image x="16" y="{image_y:.2f}" width="420" height="{height:.3f}" href="data:image/png;base64,{encoded}"/>')
        top = image_y+(gap['top']-crop_top)*scale
        bottom = image_y+(gap['bottom']+1-crop_top)*scale
        elements.append(f'<rect x="16" y="{top:.3f}" width="420" height="{bottom-top:.3f}" fill="#73818c" fill-opacity=".18"/>')
        for edge in (top, bottom):
            elements.append(f'<path d="M16 {edge:.3f}H458" stroke="#45535d" stroke-width="1.3" stroke-dasharray="6 5"/>')
        elements.append(f'<path d="M450 {top:.3f}V{bottom:.3f}M442 {top:.3f}H458M442 {bottom:.3f}H458" stroke="#29343b" stroke-width="2" fill="none"/>')
        elements.append(f'<text x="468" y="{(top+bottom)/2+10:.3f}" font-size="29" font-weight="600">{gap["pixels"]} px</text>')
        y = image_y+height+55
    height = round(y+100)
    title = html.escape(row['label'])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="580" height="{height}" viewBox="0 0 580 {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{title}: original-image line gaps</title>'
            '<desc id="desc">Two unresized lossless crops of decoded original JPEG pixels, rendered at the same scale. Shading covers only the measured gap; ink-edge guides and caliper labels sit outside the text. Numbers are inactive-row counts inside the checked horizontal strip, threshold 160, with one-based line references.</desc>'
            f'<rect width="580" height="{height}" fill="white"/>'
            '<g font-family="Arial,sans-serif" fill="#24313a">'
            f'<text x="16" y="37" font-size="29">{title}</text>'
            '<text x="16" y="74" font-size="26">Original pixels · measured blank rows</text>'
            + ''.join(elements)
            + f'<text x="16" y="{y:.2f}" font-size="25">Fixed image strip · grayscale cutoff 160</text>'
            + f'<text x="16" y="{y+36:.2f}" font-size="25">Pixel counts are not decoded symbols.</text></g></svg>\n')


def write_outputs(root: Path = ROOT, *, data_only: bool = False, check: bool = False) -> dict:
    data = build(root)
    def save(path, text):
        payload = text.encode('utf8')
        if check:
            if not path.is_file() or path.read_bytes() != payload:
                raise ValueError('Export differs: '+str(path.relative_to(root)))
        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_bytes(payload)
    save(root/'exports/line-gap-measurements.json', json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    buffer = io.StringIO(newline='')
    fields = ['region_id','page','label','threshold','from_line','to_line','top','bottom','pixels',
              'rect_x0','rect_y0','rect_x1','rect_y1','image_path']
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in data['rows']:
        for threshold, sample in row['measurements'].items():
            for gap in sample['gaps']:
                writer.writerow({'region_id':row['id'],'page':row['page'],'label':row['label'],
                                 'threshold':threshold,**gap,
                                 **dict(zip(fields[9:13],row['rect_xyxy'])), 'image_path':row['image_path']})
    save(root/'exports/line-gap-measurements.csv', buffer.getvalue())
    if not data_only:
        for row in data['rows']:
            path = root/row['overlay_path']
            save(path, overlay(root,row))
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-only', action='store_true')
    parser.add_argument('--check', action='store_true', help='Verify saved exports without overwriting them')
    args = parser.parse_args()
    data = write_outputs(data_only=args.data_only, check=args.check)
    print(f"Exported {data['coverage']['page_count']} pages / {len(data['rows'])} checked regions / {sum(len(r['gaps']) for r in data['rows'])} gaps at each of three cutoffs")


if __name__ == '__main__':
    main()
