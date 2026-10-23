"""Check the proposed 8x8 LP2-54–55 word arrangement and route ambiguity."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = HERE / 'plan.json'
SOURCE = ROOT / 'exports/unsolved-word-tokens.json'
OUTPUT = HERE / 'results.json'
FIGURE = HERE / 'word-square.svg'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_spiral():
    top, left, bottom, right = 0, 0, 7, 7
    route = []
    while left <= right and top <= bottom:
        route += [(top, x) for x in range(left, right + 1)]
        route += [(y, right) for y in range(top + 1, bottom + 1)]
        if top < bottom:
            route += [(bottom, x) for x in range(right - 1, left - 1, -1)]
        if left < right:
            route += [(y, left) for y in range(bottom - 1, top, -1)]
        top += 1; bottom -= 1; left += 1; right -= 1
    assert len(route) == len(set(route)) == 64
    return route


def routes():
    out = []
    for turn in range(4):
        for reflection in (False, True):
            path = []
            for row, col in base_spiral():
                for _ in range(turn):
                    row, col = col, 7 - row
                if reflection:
                    col = 7 - col
                path.append(8 * row + col)
            assert len(set(path)) == 64
            out.append({'turns_clockwise': turn, 'reflected': reflection,
                        'start_cell': path[0] + 1, 'first_eight_cells': [n + 1 for n in path[:8]],
                        'last_cell': path[-1] + 1,
                        'cell_order': [n + 1 for n in path]})
    assert len({tuple(x['cell_order']) for x in out}) == 8
    return out


def report():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    for dep in plan['inputs']:
        if digest(ROOT / dep['path']) != dep['sha256']:
            raise ValueError('Input changed: ' + dep['path'])
    words = [item for item in json.loads(SOURCE.read_text(encoding='utf-8'))
             if item['start']['page'] in ('lp2-54', 'lp2-55')]
    assert len(words) == 66
    excluded = words[:2]
    assert [x['rune_length'] for x in excluded] == [1, 8]
    remaining = words[2:]
    assert len(remaining) == 64
    by_start = {page: sum(x['start']['page'] == page for x in remaining)
                for page in ('lp2-54', 'lp2-55')}
    assert by_start == {'lp2-54': 48, 'lp2-55': 16}
    crossing = [x['ordinal'] for x in remaining if x['start']['page'] != x['end']['page']]
    return {'schema':'liberpedia-lp2-54-55-word-square-v1', 'plan_sha256':digest(PLAN),
            'source_sha256':digest(SOURCE), 'original_words':66,
            'excluded_opening':[{'ordinal':x['ordinal'], 'rune_length':x['rune_length']} for x in excluded],
            'remaining_words':64, 'starts_by_page':by_start,
            'cross_page_word_ordinals':crossing,
            'grid':[{'cell':i+1, 'word_ordinal':x['ordinal'], 'page_of_start':x['start']['page'],
                     'rune_length':x['rune_length']} for i,x in enumerate(remaining)],
            'distinct_simple_spiral_routes':8,'spiral_routes':routes()}


def figure(result):
    parts=[]
    for item in result['grid']:
        index=item['cell']-1; row,col=divmod(index,8)
        x,y=22+41*col,75+41*row
        color='#e8edf0' if row<6 else '#dcebf2'
        parts.append(f'<rect x="{x}" y="{y}" width="37" height="37" fill="{color}" stroke="#a5b2b9"/>')
        parts.append(f'<text x="{x+18.5}" y="{y+23}" text-anchor="middle" class="cell">{item["cell"]:02}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="370" height="464" viewBox="0 0 370 464" role="img" '
            'aria-label="Eight-by-eight word grid: first six rows start on LP2-54 and last two on LP2-55">'
            '<style>text{font:14px system-ui,sans-serif;fill:#24333b}.title{font-size:18px;font-weight:650}.cell{font-size:14px;font-weight:600}</style>'
            '<rect width="100%" height="100%" fill="white"/>'
            '<text x="20" y="27" class="title">64 words after the red opening</text>'
            '<text x="20" y="50">48 start on LP2-54 · 16 on LP2-55</text>'
            + ''.join(parts) +
            '<text x="22" y="438">Cells show word order, not a cipher route.</text></svg>\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true')
    args=p.parse_args(); result=report(); image=figure(result)
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding='utf-8'))==result
        assert FIGURE.read_text(encoding='utf-8')==image
        print('PASS lp2-54-55-word-square')
    else:
        OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        FIGURE.write_text(image,encoding='utf-8',newline='\n')
        print('Wrote results.json and word-square.svg')


if __name__=='__main__':
    main()
