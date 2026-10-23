"""Recount F-omitted signed-message transliterations and all symbol omissions."""
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
import later_message_sums  # noqa: E402


def prime(n: int) -> bool:
    if n < 2:
        return False
    for divisor in range(2, math.isqrt(n) + 1):
        if n % divisor == 0:
            return False
    return True


def report() -> dict:
    base = later_message_sums.report()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    streams = (base['body_2016']['indices'], base['body_2017']['indices'])
    original = [len(stream) for stream in streams]
    if original != plan['reported_original_counts']:
        raise ValueError('Original lengths differ from frozen report')
    rows = []
    for entry in alphabet:
        index = entry['index']
        kept = [len(stream) - stream.count(index) for stream in streams]
        removed = [stream.count(index) for stream in streams]
        rows.append({'index': index, 'rune': entry['rune'], 'omitted': removed,
                     'remaining': kept, 'both_prime': all(prime(n) for n in kept)})
    f = rows[0]
    if f['remaining'] != plan['reported_f_omitted_counts']:
        raise ValueError('F-omitted counts differ from frozen report')
    return {
        'source_input_sha256': base['input_sha256'],
        'encoding_script_sha256': hashlib.sha256((ROOT / 'scripts/later_message_sums.py').read_bytes()).hexdigest(),
        'original_lengths': original,
        'original_are_prime': [prime(n) for n in original],
        'f_omitted': f,
        'all_symbol_omissions': rows,
        'both_prime_symbols': [row['index'] for row in rows if row['both_prime']],
        'both_prime_symbol_count': sum(row['both_prime'] for row in rows),
        'alphabet_size': len(rows),
        'limit': 'The signed bodies contain Latin letters, not runes. These counts depend on the declared GP encoding and do not demonstrate a manuscript cipher.'
    }


def figure(result: dict) -> str:
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 226" role="img" aria-labelledby="t d">',
           '<title id="t">Signed-message lengths before and after one rune omission</title>',
           '<desc id="d">Under one GP transliteration, 2016 has 177 runes and 2017 has 45. Removing F leaves prime lengths 173 and 41. Removing W also leaves prime lengths, 173 and 43.</desc>',
           '<rect width="360" height="226" fill="#f5f6f7"/>',
           '<text x="14" y="29" fill="#202a30" font-family="system-ui,sans-serif" font-size="17" font-weight="700">Prime lengths after omission</text>',
           '<text x="14" y="52" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">Signed-message bodies · declared GP encoding</text>',
           '<text x="14" y="85" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">Rule</text>',
           '<text x="232" y="85" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">2016</text>',
           '<text x="301" y="85" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">2017</text>']
    entries = [('Original', result['original_lengths'], False), ('Omit F', result['all_symbol_omissions'][0]['remaining'], True), ('Omit W', result['all_symbol_omissions'][7]['remaining'], True)]
    for ri, (label, nums, highlighted) in enumerate(entries):
        y = 115 + 33*ri
        if highlighted:
            out.append(f'<rect x="10" y="{y-20}" width="340" height="27" fill="#e3eef3"/>')
        for x, value in [(14, label), (236, nums[0]), (305, nums[1])]:
            out.append(f'<text x="{x}" y="{y}" fill="#202a30" font-family="system-ui,sans-serif" font-size="14" font-weight="{700 if highlighted else 400}">{value}</text>')
    out.append('<text x="14" y="215" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">2 of 29 single-rune omissions give two primes.</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    svg = figure(result)
    output = HERE / 'results.json'
    visual = HERE / 'omission-counts.svg'
    if args.check:
        if json.loads(output.read_text(encoding='utf-8')) != result or visual.read_text(encoding='utf-8') != svg:
            raise SystemExit('Saved result or figure differs')
    else:
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        visual.write_text(svg, encoding='utf-8', newline='\n')
    print(result['original_lengths'], result['f_omitted']['remaining'], result['both_prime_symbols'])
