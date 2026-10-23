"""Replay the exact six positions reached by the pinned QuagMirror draft."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PLAN = HERE / "plan.json"
OUTPUT = HERE / "results.json"
FIGURE = HERE / "six-rune-trace.svg"
PRIMES = (2, 3, 5, 7, 11, 13)
FRAGMENTS = ('F', 'U', 'TH', 'O', 'R', 'C', 'G', 'W', 'H', 'N', 'I', 'J', 'EO', 'P', 'X', 'S', 'T', 'B', 'E', 'M', 'L', 'ING', 'OE', 'D', 'A', 'AE', 'Y', 'IA', 'EA')


def mobius(n: int) -> int:
    if n < 1:
        raise ValueError(n)
    sign = 1
    divisor = 2
    while divisor * divisor <= n:
        if n % divisor == 0:
            n //= divisor
            sign = -sign
            if n % divisor == 0:
                return 0
        divisor += 1
    return -sign if n > 1 else sign


def at_shift(value: int, mu: int) -> int:
    return 28 - value if mu == 0 else -value if mu == -1 else value


def replay() -> dict:
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
    indices = {entry['rune']: entry['index'] for entry in alphabet}
    page = json.loads((ROOT / 'data/pages/lp2-00.json').read_text(encoding='utf-8'))
    first = [indices[c] for c in page['raw'] if c in indices][:6]
    if first != plan['ciphertext_indices']:
        raise ValueError('First six LP2-00 runes differ from pinned source array')
    tables = plan['mirror_tables']
    if set(tables) != {'AA', 'AP', 'AC', 'PA', 'PP', 'PC', 'CA', 'CP', 'CC'} or any(sorted(t) != list(range(29)) for t in tables.values()):
        raise ValueError('Nine source mirror tables must each permute 0..28')
    names = {-1: 'C', 0: 'A', 1: 'P'}
    previous_cipher = previous_plain = 0
    previous_mobius = previous_totient_mobius = 1
    rows = []
    for pos, (cipher, prime) in enumerate(zip(first, PRIMES)):
        totient = prime - 1
        mu_position = mobius(pos + 1)
        mu_totient = mobius(totient)
        at = (cipher - at_shift(previous_cipher, previous_mobius) - at_shift(previous_plain, previous_totient_mobius)) % 29
        left, right = mu_totient, previous_totient_mobius
        if pos == 0:
            at, left, right = 15, 1, 1
        if pos == 1:
            left = right = -1
        table = names[left] + names[right]
        plain = tables[table][at]
        rows.append({'position': pos, 'cipher_index': cipher, 'prime': prime,
                     'mobius_position': mu_position, 'mobius_totient': mu_totient,
                     'autokey_index': at, 'mirror': table, 'plaintext_index': plain,
                     'latin_fragment': FRAGMENTS[plain]})
        previous_cipher, previous_plain = cipher, plain
        previous_mobius, previous_totient_mobius = mu_position, mu_totient
    return {
        'source_commit': plan['source_commit'],
        'source_sha256': plan['source_sha256'],
        'page': 'lp2-00',
        'positions_executed': len(rows),
        'rows': rows,
        'autokey_indices': [row['autokey_index'] for row in rows],
        'plaintext_indices': [row['plaintext_index'] for row in rows],
        'transliteration': ''.join(row['latin_fragment'] for row in rows),
        'matches_source_stdout': [row['autokey_index'] for row in rows] == plan['expected_autokey_indices'] and [row['plaintext_index'] for row in rows] == plan['expected_plaintext_indices'] and ''.join(row['latin_fragment'] for row in rows) == plan['expected_transliteration'],
        'input_sha256': {'data/index.json': hashlib.sha256((ROOT / 'data/index.json').read_bytes()).hexdigest(), 'data/pages/lp2-00.json': hashlib.sha256((ROOT / 'data/pages/lp2-00.json').read_bytes()).hexdigest()},
        'limit': 'This source file breaks after six runes. Reproducing DCBWJO does not test a complete plaintext or the other changing drafts in the repository.'
    }


def figure(rows: list[dict]) -> str:
    def esc(s: str) -> str:
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 286" role="img" aria-labelledby="title desc">',
           '<title id="title">QuagMirror draft: six processed runes</title>',
           '<desc id="desc">Each column traces one archived LP2-00 cipher index through the source autokey, mirror choice, and output fragment. The source script stops at six.</desc>',
           '<rect width="360" height="286" fill="#f5f6f7"/>',
           '<text x="14" y="30" fill="#202a30" font-family="system-ui,sans-serif" font-size="17" font-weight="700">Six processed runes</text>',
           '<text x="14" y="52" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">LP2-00 · pinned QuagMirror draft</text>']
    labels = [('Cipher', 'cipher_index'), ('Autokey', 'autokey_index'), ('Mirror', 'mirror'), ('Output', 'plaintext_index'), ('Latin', 'latin_fragment')]
    for ri, (label, key) in enumerate(labels):
        y = 98 + 32 * ri
        out.append(f'<text x="14" y="{y}" fill="#52616a" font-family="system-ui,sans-serif" font-size="13">{label}</text>')
        for ci, row in enumerate(rows):
            x = 116 + ci * 45
            out.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="#202a30" font-family="system-ui,sans-serif" font-size="13" font-weight="600">{esc(str(row[key]))}</text>')
    out.append('<line x1="14" x2="346" y1="250" y2="250" stroke="#b9c4ca"/>')
    out.append('<text x="14" y="273" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">DCBWJO · source stops after six</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = replay()
    if not result['matches_source_stdout']:
        raise SystemExit('Independent replay does not match the pinned source output')
    svg = figure(result['rows'])
    if args.check:
        if json.loads(OUTPUT.read_text(encoding='utf-8')) != result or FIGURE.read_text(encoding='utf-8') != svg:
            raise SystemExit('Saved results or figure differ')
    else:
        OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        FIGURE.write_text(svg, encoding='utf-8', newline='\n')
    print(result['transliteration'], result['matches_source_stdout'])
