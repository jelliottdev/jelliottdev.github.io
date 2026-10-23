"""Recheck the reported 331/133 pointer and enumerate alternative cuts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_464_pointer import report as source_audit  # noqa: E402


def is_prime(n: int) -> bool:
    return n > 1 and all(n % d for d in range(2, math.isqrt(n) + 1))


def make_report() -> dict:
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    base = source_audit()
    values = base['word_prime_sums']
    words = base['word_readings']
    total = sum(values)
    running = 0
    cuts = []
    for k, value in enumerate(values[:-1], start=1):
        running += value
        cuts.append({'after_forward_word': k, 'reverse_index_of_next': 464 - k,
                     'left_sum': running, 'right_sum': total - running,
                     'left_prime': is_prime(running), 'right_prime': is_prime(total - running)})
    pairs = [cut for cut in cuts if words[cut['after_forward_word']-1:cut['after_forward_word']+1] == plan['reported_pair']]
    target = cuts[330]
    return {
        'total_words': len(words), 'gp_total': total,
        'pointer_forward': 331, 'pointer_reverse': 133,
        'pointer_pair': words[330:332],
        'observed_left_sum': target['left_sum'], 'reported_left_sum': plan['reported_block_gp_sums'][0],
        'observed_right_sum': target['right_sum'], 'reported_right_sum': plan['reported_block_gp_sums'][1],
        'left_difference': target['left_sum'] - plan['reported_block_gp_sums'][0],
        'left_prime': target['left_prime'], 'right_prime': target['right_prime'],
        'study_here_occurrences': pairs,
        'all_cuts': 463,
        'prime_left_cuts': sum(c['left_prime'] for c in cuts),
        'prime_right_cuts': sum(c['right_prime'] for c in cuts),
        'both_prime_cuts': [c['after_forward_word'] for c in cuts if c['left_prime'] and c['right_prime']],
        'input_sha256': base['input_sha256'],
        'source_audit_script_sha256': hashlib.sha256((ROOT / 'scripts/audit_464_pointer.py').read_bytes()).hexdigest(),
        'limit': 'The five phrase locations and cut counts describe this pre-existing reading. No selection probability or LP2 cipher rule is inferred.'
    }


def draw(r: dict) -> str:
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 302" role="img" aria-labelledby="t d">',
           '<title id="t">Five STUDY HERE locations in the 464-word reading</title>',
           '<desc id="d">The phrase occurs five times. At the selected cut after word 331, the last 133 ciphertext words sum to the reported prime 26893, but the first 331 sum to 72065, not the reported 71963.</desc>',
           '<rect width="360" height="302" fill="#f5f6f7"/>',
           '<text x="14" y="28" fill="#202a30" font-family="system-ui,sans-serif" font-size="17" font-weight="700">STUDY HERE appears five times</text>',
           '<text x="14" y="50" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">Forward / reverse word positions</text>']
    for pair in r['study_here_occurrences']:
        k = pair['after_forward_word']
        y = 82 + r['study_here_occurrences'].index(pair) * 30
        selected = k == 331
        color = '#215d79' if selected else '#788b98'
        if selected:
            out.append(f'<rect x="10" y="{y-18}" width="340" height="25" fill="#e3eef3"/>')
        out += [f'<circle cx="21" cy="{y-4}" r="5" fill="{color}"/>',
                f'<text x="38" y="{y}" fill="#202a30" font-family="system-ui,sans-serif" font-size="14" font-weight="{700 if selected else 400}">{k} / {pair["reverse_index_of_next"]}</text>']
    out += ['<line x1="14" x2="346" y1="230" y2="230" stroke="#b9c4ca"/>',
            '<text x="14" y="251" fill="#202a30" font-family="system-ui,sans-serif" font-size="13">First 331: 72,065 ≠ reported 71,963</text>',
            '<text x="14" y="274" fill="#202a30" font-family="system-ui,sans-serif" font-size="13">Last 133: 26,893 = reported 26,893</text>',
            '<text x="14" y="294" fill="#52616a" font-family="system-ui,sans-serif" font-size="11">The selected pair is one of five in solved LP1 text.</text>', '</svg>']
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = make_report()
    svg = draw(result)
    output = HERE / 'results.json'
    figure = HERE / 'pointer-locations.svg'
    if args.check:
        if json.loads(output.read_text(encoding='utf-8')) != result or figure.read_text(encoding='utf-8') != svg:
            raise SystemExit('Saved output differs from recomputation')
    else:
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        figure.write_text(svg, encoding='utf-8', newline='\n')
    print('phrase locations:', len(result['study_here_occurrences']), 'reported left difference:', result['left_difference'])
