"""Measure sensitivity of LP2 rune-token statistics to unresolved page edges."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def measure():
    plan_bytes = (HERE / 'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    for item in plan['inputs']:
        assert digest((ROOT / item['path']).read_bytes()) == item['sha256'], item['path']
    alphabet = {entry['rune'] for entry in json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']}
    pattern = re.compile('[' + ''.join(sorted(alphabet)) + "]+(?:'['" + ''.join(sorted(alphabet)) + ']+)*')
    pages = [(ROOT / f'text/lp2-{n:02d}.txt').read_text(encoding='utf-8').replace('/', '').replace('\r', '').replace('\n', '') for n in range(56)]
    candidates = [n for n in range(55) if pages[n] and pages[n+1] and pages[n][-1] in alphabet and pages[n+1][0] in alphabet]
    assert len(candidates) == 32

    def tokens(split):
        pieces = [pages[0]]
        for n in range(55):
            pieces.append(' ' if n in split else '')
            pieces.append(pages[n+1])
        return [m.group() for m in pattern.finditer(''.join(pieces))]

    def summary(items):
        lengths = [sum(ch in alphabet for ch in token) for token in items]
        hist = Counter(lengths)
        return {'token_count': len(items), 'max_length': max(lengths),
                'histogram': {str(k): hist[k] for k in sorted(hist)},
                'long_tokens_10_plus': sum(x >= 10 for x in lengths),
                'repeated_token_types': sum(v > 1 for v in Counter(items).values()),
                'eleven_eleven_ten_windows': sum(lengths[i:i+3] == [11, 11, 10] for i in range(len(lengths)-2))}

    joined = summary(tokens(set()))
    separated = summary(tokens(set(candidates)))
    rows = []
    for n in candidates:
        changed = summary(tokens({n}))
        rows.append({'edge': f'LP2-{n:02d}/{n+1:02d}', 'joined_token_count': joined['token_count'],
                     'split_token_count': changed['token_count'],
                     'split_max_length': changed['max_length'],
                     'split_long_tokens_10_plus': changed['long_tokens_10_plus'],
                     'split_eleven_eleven_ten_windows': changed['eleven_eleven_ten_windows']})
    return {'schema': 'liberpedia-page-join-sensitivity-v1', 'plan_sha256': digest(plan_bytes),
            'scope': 'LP2-00–55 archived text; all 32 rune-to-rune page edges only.',
            'rule': 'Remove slash and CR/LF row wraps; preserve other delimiters. Compare no added page delimiter with a space at all 32 candidate edges, and separately at each edge. Headings retained.',
            'candidate_edges': [f'LP2-{n:02d}/{n+1:02d}' for n in candidates],
            'all_joined': joined, 'all_candidates_separated': separated,
            'single_edge_splits': rows,
            'limitation': 'Candidate edges are transcription character classes, not confirmed word joins. Whole-stream rune counts and IoC are invariant to spaces added at page boundaries. Neither endpoint is asserted to match manuscript punctuation.'}


def figure(result):
    a, b = result['all_joined']['histogram'], result['all_candidates_separated']['histogram']
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400" role="img" aria-labelledby="title desc">',
             '<title id="title">LP2 token length sensitivity to page-edge separation</title>',
             '<desc id="desc">Side-by-side counts for joined and separated candidate edges. The same runes are used in both cases.</desc>',
             '<rect width="640" height="400" fill="#faf9f5"/>',
             '<g font-family="Arial,sans-serif" fill="#233946">',
             '<text x="24" y="32" font-size="21">What changes at page breaks?</text>',
             '<text x="24" y="57" font-size="13">LP2-00–55 · same rune stream · 32 candidate edges</text>']
    for count in (0, 200, 400, 600, 800):
        y = 324 - count * .29
        lines += [f'<path d="M52 {y:.1f}H616" stroke="#d9dddb"/>', f'<text x="45" y="{y+4:.1f}" font-size="12" text-anchor="end">{count}</text>']
    for length in range(1, 15):
        x = 55 + (length-1)*40
        for offset, data, color in ((0, a, '#315f73'), (17, b, '#b16a42')):
            h = int(data.get(str(length), 0)) * .29
            lines.append(f'<rect x="{x+offset}" y="{324-h:.1f}" width="15" height="{h:.1f}" fill="{color}"/>')
        lines.append(f'<text x="{x+16}" y="344" font-size="12" text-anchor="middle">{length}</text>')
    lines += ['<rect x="60" y="365" width="14" height="14" fill="#315f73"/><text x="82" y="377" font-size="13">Joined</text>',
              '<rect x="164" y="365" width="14" height="14" fill="#b16a42"/><text x="186" y="377" font-size="13">32 candidates separated</text>', '</g></svg>']
    return '\n'.join(lines)+'\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    result = measure()
    chart = figure(result)
    if args.check:
        assert result == json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        assert chart == (HERE/'token-lengths.svg').read_text(encoding='utf-8')
        print('PASS: page-edge sensitivity report and figure reproduce')
    else:
        (HERE/'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
        (HERE/'token-lengths.svg').write_text(chart, encoding='utf-8', newline='\n')
        print(json.dumps({'joined': result['all_joined'], 'separated': result['all_candidates_separated']}, indent=2))


if __name__ == '__main__':
    main()
