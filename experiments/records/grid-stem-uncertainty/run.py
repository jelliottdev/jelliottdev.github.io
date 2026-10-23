"""Audit the ten visually bare I/l stems in the LP2-49–51 grids."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
GRID_ROW = re.compile(r"[0-9A-Za-z]{2}(?:[\t -]+[0-9A-Za-z]{2}){7}/?")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid(text, count):
    rows = [re.split(r"[\t -]+", line.rstrip("/")) for line in text.splitlines()
            if GRID_ROW.fullmatch(line)]
    assert len(rows) == count and all(len(row) == 8 for row in rows)
    return rows


def byte(token):
    value = 60 * DIGITS.index(token[0]) + DIGITS.index(token[1])
    assert 0 <= value <= 255
    return value


def svg(cells, rows_by_page):
    width, top, pitch, row_h = 472, 60, 46, 28
    marked = {(c['page'], c['row'], c['column']): c for c in cells}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 1190" role="img" aria-labelledby="title desc">',
             '<title id="title">Grid cells with case-sensitive bare stems</title>',
             '<desc id="desc">Ten I-or-l cells across LP2-49 to LP2-51 are highlighted. One additional S-or-s transcription disagreement is marked separately.</desc>',
             '<rect width="472" height="1190" fill="#ffffff"/>',
             '<g font-family="Arial, sans-serif" fill="#202c33">',
             '<text x="18" y="31" font-size="18" font-weight="bold">Case-sensitive grid positions</text>',
             '<text x="18" y="50" font-size="11">Coordinates follow the printed 8-column grids; this is a map, not a reading route.</text>']
    y = top
    for page, row_count in rows_by_page.items():
        parts += [f'<text x="18" y="{y+17}" font-size="15" font-weight="bold">{page.upper()}</text>']
        y += 24
        for col in range(1, 9):
            parts.append(f'<text x="{55+(col-1)*pitch+19}" y="{y+9}" text-anchor="middle" font-size="10" fill="#60717b">{col}</text>')
        y += 15
        for row in range(1, row_count + 1):
            parts.append(f'<text x="46" y="{y+19}" text-anchor="end" font-size="10" fill="#60717b">{row}</text>')
            for col in range(1, 9):
                item = marked.get((page, row, col))
                other = page == 'lp2-50' and row == 12 and col == 5
                fill = '#dcebf1' if item else ('#e2e6ea' if other else '#eef1f4')
                outline = ' stroke="#596b78" stroke-width="1" stroke-dasharray="3 2"' if other else ''
                parts.append(f'<rect x="{55+(col-1)*pitch}" y="{y}" width="39" height="24" rx="2" fill="{fill}"{outline}/>')
                if item:
                    parts.append(f'<text x="{55+(col-1)*pitch+19.5}" y="{y+17}" text-anchor="middle" font-size="13" font-weight="bold">{item["wiki_token"]}</text>')
                elif other:
                    parts.append(f'<text x="{55+(col-1)*pitch+19.5}" y="{y+17}" text-anchor="middle" font-size="13" font-weight="bold">2S</text>')
            y += row_h
        y += 13
    parts += ['<rect x="18" y="1150" width="13" height="13" fill="#dcebf1"/>',
              '<text x="38" y="1161" font-size="11">I/l bare stem</text>',
              '<rect x="167" y="1150" width="13" height="13" fill="#e2e6ea" stroke="#596b78" stroke-width="1" stroke-dasharray="3 2"/>',
              '<text x="187" y="1161" font-size="11">S/s source disagreement</text>',
              '</g></svg>']
    assert y < 1140, y
    return ('\n'.join(parts) + '\n').encode('utf-8')


def report():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for entry in plan['inputs']:
        assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
    with (ROOT / 'exports/alphanumeric-grids.csv').open(encoding='utf-8', newline='') as f:
        wiki = list(csv.DictReader(f))
    assert len(wiki) == 256 and [int(c['sequence']) for c in wiki] == list(range(1, 257))
    source = (ROOT / 'exports/sources/cicada-2014-seventh-onion/0-55.jpg.runes.txt').read_text(encoding='utf-8')
    blocks = re.split(r'(?m)^%\s*$', source)
    assert len(blocks) == 56
    source_grids = {f'lp2-{n:02d}': grid(blocks[n], {49:10, 50:13, 51:9}[n]) for n in (49,50,51)}
    cells = []
    for entry in wiki:
        token = entry['token']
        if token[-1] not in 'Il':
            continue
        page, row, col = entry['page'], int(entry['row']), int(entry['column'])
        archive = source_grids[page][row-1][col-1]
        alternatives = [token[0] + 'I', token[0] + 'l']
        cells.append({'page':page,'row':row,'column':col,'sequence':int(entry['sequence']),
                      'wiki_token':token,'archive_token':archive,
                      'visual_class':'bare vertical stem; no visible dot or L foot',
                      'alternatives':alternatives,
                      'base60_bytes':[byte(t) for t in alternatives],
                      'differing_bits':(byte(alternatives[0]) ^ byte(alternatives[1])).bit_count()})
    assert [(c['page'],c['row'],c['column']) for c in cells] == [tuple(x) for x in plan['stem_coordinates']]
    assert len(cells) == 10 and all(c['differing_bits'] > 0 for c in cells)
    base = [entry['token'] for entry in wiki]
    variants = []
    for mask in range(1 << len(cells)):
        candidate = base.copy()
        for i, cell in enumerate(cells):
            candidate[cell['sequence']-1] = cell['alternatives'][(mask >> i) & 1]
        values = [byte(token) for token in candidate]
        variants.append({'mask':mask,'distinct_tokens':len(set(candidate)),
                         'one_bits':sum(v.bit_count() for v in values),
                         'even_bytes':sum(v % 2 == 0 for v in values)})
    original = {'distinct_tokens':len(set(base)),
                'one_bits':sum(byte(token).bit_count() for token in base),
                'even_bytes':sum(byte(token) % 2 == 0 for token in base)}
    result = {'schema':'liberpedia-grid-stem-uncertainty-v1','plan_sha256':sha(HERE/'plan.json'),
              'grid_cells':len(wiki),'stem_cells':cells,
              'separate_case_disagreement':{'page':'lp2-50','row':12,'column':5,'archive_token':'2s','wiki_token':'2S',
                                            'visual_note':'Image shows an uppercase S-shaped form; this is separate from I/l stems.'},
              'wiki_metrics':original,
              'alternative_scope':'Only the ten listed I/l stems may toggle independently; all other 246 cells remain at wiki values, including 2S.',
              'variant_count':len(variants),
              'ranges':{key:[min(v[key] for v in variants),max(v[key] for v in variants)]
                        for key in original},
              'variants':variants,
              'limits':['Visual classification is manual and should be reviewed against both preserved JPEG copies.',
                        'Independent toggles are a sensitivity envelope, not 1024 equally plausible authorial spellings.',
                        'This does not audit 0/O or every other possible glyph ambiguity.',
                        'The byte calculations require the conditional base-60 digit alphabet and unsigned-byte interpretation.']}
    return result, svg(cells, {'lp2-49':10,'lp2-50':13,'lp2-51':9})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    result, figure = report()
    encoded=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    outputs={HERE/'results.json':encoded,HERE/'stem-map.svg':figure}
    if args.check:
        for path, expected in outputs.items():
            assert path.read_bytes()==expected, path
    else:
        for path, data in outputs.items():path.write_bytes(data)
    print('Checked 10 stem cells and',result['variant_count'],'bounded byte variants:',result['ranges'])


if __name__=='__main__':main()
