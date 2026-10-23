"""Compare LP2-16–22's 59-square prime-digit count with every seven-page window."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = HERE / 'plan.json'
OUTPUT = HERE / 'results.json'
FIGURE = HERE / 'windows.svg'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    for dep in plan['inputs']:
        if digest(ROOT / dep['path']) != dep['sha256']:
            raise ValueError('Changed input: ' + dep['path'])
    index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
    prime = {item['rune']: item['prime'] for item in index['alphabet']}
    page_counts = []
    alternatives = {'runes': [], 'index_0_digits': [], 'index_1_digits': []}
    position = {item['rune']: i for i, item in enumerate(index['alphabet'])}
    for number in range(56):
        path = ROOT / f'text/lp2-{number:02}.txt'
        raw = path.read_text(encoding='utf-8')
        runes = [char for char in raw if char in prime]
        unknown = {char for char in raw if '\u16a0' <= char <= '\u16ff'} - prime.keys()
        if unknown:
            raise ValueError(f'Unknown rune in {path}: {unknown}')
        page_counts.append(sum(len(str(prime[char])) for char in runes))
        alternatives['runes'].append(len(runes))
        alternatives['index_0_digits'].append(sum(len(str(position[char])) for char in runes))
        alternatives['index_1_digits'].append(sum(len(str(position[char] + 1)) for char in runes))
    windows = []
    for first in range(50):
        total = sum(page_counts[first:first + 7])
        lo = math.isqrt(total)
        is_square = lo * lo == total
        distance = min(total - lo * lo, (lo + 1)**2 - total)
        windows.append({'first': first, 'last': first + 6, 'prime_digits': total,
                        'square': is_square, 'square_root': lo if is_square else None,
                        'distance_to_nearest_square': distance})
    target = windows[16]
    assert target['prime_digits'] == 3481 == 59**2
    other_square_windows = {}
    for name, counts in alternatives.items():
        other_square_windows[name] = []
        for first in range(50):
            total = sum(counts[first:first+7])
            root = math.isqrt(total)
            if root * root == total:
                other_square_windows[name].append({'first': first, 'last': first+6,
                                                   'count': total, 'square_root': root})
    return {'schema':'liberpedia-lp2-seven-page-square-fits-v1',
            'plan_sha256':digest(PLAN), 'page_prime_digit_counts':page_counts,
            'window_width_pages':7, 'window_count':len(windows), 'windows':windows,
            'target':target, 'square_windows':[x for x in windows if x['square']],
            'other_representation_square_windows': other_square_windows,
            'near_square_window_count_at_target_distance':sum(x['distance_to_nearest_square'] <= target['distance_to_nearest_square'] for x in windows)}


def figure(report):
    items = report['windows']
    w,h=380,306
    top=48; plot_h=190; scale=plot_h/max(x['prime_digits'] for x in items)
    bars=[]
    for x in items:
        left=25+x['first']*6.6
        bar_h=x['prime_digits']*scale
        fill='#205c7a' if x['first']==16 else ('#8aa0ac' if x['square'] else '#ced5d9')
        bars.append(f'<rect x="{left:.1f}" y="{top+plot_h-bar_h:.1f}" width="4.6" height="{bar_h:.1f}" fill="{fill}"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="380" height="306" viewBox="0 0 380 306" role="img" '
            'aria-label="Decimal prime-digit counts for all 50 seven-page windows; LP2-16 through 22 is one exact square">'
            '<style>text{font:13px system-ui,sans-serif;fill:#26343b}.title{font-size:18px;font-weight:650}</style>'
            '<rect width="100%" height="100%" fill="white"/>'
            '<text x="19" y="24" class="title">Seven-page digit counts</text>'
            + ''.join(bars) +
            '<line x1="23" y1="238" x2="357" y2="238" stroke="#7f8d94"/>'
            '<text x="22" y="258">00</text><text x="339" y="258">49</text>'
            '<text x="19" y="283">Start page · blue: LP2-16–22 = 59²</text>'
            '</svg>\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report(); image=figure(result)
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding='utf-8'))==result
        assert FIGURE.read_text(encoding='utf-8')==image
        print('PASS lp2-seven-page-square-fits')
    else:
        OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        FIGURE.write_text(image,encoding='utf-8',newline='\n')
        print('Wrote results.json and windows.svg')


if __name__=='__main__':
    main()
