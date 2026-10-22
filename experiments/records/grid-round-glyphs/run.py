"""Make a coordinate census and unscaled 0/O glyph contact sheets."""
import argparse
import csv
import hashlib
import io
import json
from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw, __version__ as PILLOW_VERSION

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx'
# Centers calibrated on 600x900 views of the 2400x3600 originals.
CENTERS = {
    49: {'x': [186, 220, 251, 283, 315, 346, 378, 410], 'y0': 322, 'step': 44.5, 'rows': 10},
    50: {'x': [180, 212, 243, 275, 306, 337, 369, 401], 'y0': 167, 'step': 44.4, 'rows': 13},
    51: {'x': [187, 218, 249, 280, 311, 342, 374, 405], 'y0': 167, 'step': 44.3, 'rows': 9},
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def value(token):
    return 60 * ALPHABET.index(token[0]) + ALPHABET.index(token[1])

def build():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for source in plan['source_pins']:
        assert sha((ROOT / source['path']).read_bytes()) == source['sha256'], source['path']
    with (ROOT / 'exports/alphanumeric-grids.csv').open(encoding='utf-8', newline='') as f:
        entries = list(csv.DictReader(f))
    assert len(entries) == 256 and [int(e['sequence']) for e in entries] == list(range(1, 257))
    cases = []
    outputs = {}
    for page, spec in CENTERS.items():
        rows = [e for e in entries if e['page'] == f'lp2-{page}' and any(ch in '0O' for ch in e['token'])]
        assert max(int(e['row']) for e in rows) <= spec['rows']
        source = ROOT / f'images/lp2-{page}.jpg'
        with Image.open(io.BytesIO(source.read_bytes())) as im:
            assert im.size == (2400, 3600)
            sheet = Image.new('RGB', (4 * 252, ceil(len(rows) / 4) * 162), 'white')
            draw = ImageDraw.Draw(sheet)
            for index, entry in enumerate(rows):
                row, col = int(entry['row']), int(entry['column'])
                cx = spec['x'][col - 1] * 4
                cy = round((spec['y0'] + (row - 1) * spec['step']) * 4)
                box = (cx - 108, cy - 59, cx + 108, cy + 59)
                tile_x, tile_y = (index % 4) * 252, (index // 4) * 162
                sheet.paste(im.crop(box).convert('RGB'), (tile_x + 18, tile_y + 29))
                draw.rectangle((tile_x, tile_y, tile_x + 251, tile_y + 161), outline='#bbb9b1')
                draw.text((tile_x + 16, tile_y + 7), f'{page}  row {row}  col {col}', fill='#26343c')
                token = entry['token']
                alternatives = []
                for pos, character in enumerate(token):
                    if character in '0O':
                        alt = token[:pos] + ('O' if character == '0' else '0') + token[pos + 1:]
                        alternatives.append({'character_index': pos + 1, 'read_as': character,
                                             'alternate_token': alt, 'alternate_base60': value(alt),
                                             'alternate_is_byte': value(alt) <= 255})
                cases.append({'sequence': int(entry['sequence']), 'page': entry['page'],
                              'row': row, 'column': col, 'wiki_token': token,
                              'wiki_base60': value(token), 'crop_box_xyxy': list(box),
                              'round_marks': alternatives})
            with io.BytesIO() as buf:
                sheet.save(buf, format='PNG')
                outputs[HERE / f'round-glyphs-lp2-{page}.png'] = buf.getvalue()
    assert len(cases) == 70 and sum(len(c['round_marks']) for c in cases) == 72
    result = {'schema': 'liberpedia-grid-round-glyphs-v1', 'plan_sha256': sha((HERE / 'plan.json').read_bytes()),
              'pillow_version': PILLOW_VERSION, 'cell_count': len(cases), 'mark_count': 72,
              'zero_marks': sum(m['read_as'] == '0' for c in cases for m in c['round_marks']),
              'capital_o_marks': sum(m['read_as'] == 'O' for c in cases for m in c['round_marks']),
              'cases': cases,
              'visual_review': 'Manual contact-sheet pass found no definite conflict; independent human review pending.',
              'limits': plan['limits']}
    outputs[HERE / 'results.json'] = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    return outputs

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = build()
    for path, content in outputs.items():
        if args.check:
            assert path.read_bytes() == content, path
        else:
            path.write_bytes(content)
    print('Checked 70 cells and 72 round marks across three source-pixel contact sheets.')

if __name__ == '__main__':
    main()
