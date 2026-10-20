"""Find fixed one-to-one substitution-compatible rune windows on one page.

Separate proposed rune labels with spaces: --crib "F U F U TH".
This ignores separators, includes headings, and tests overlapping windows.
It does not find English words or test a particular cipher/key.
"""
import argparse
import hashlib
import json
from pathlib import Path
from rune_ngrams import indexed_runes, occurrence

ROOT = Path(__file__).resolve().parents[1]


def pattern(symbols):
    seen = {}
    return tuple(seen.setdefault(symbol, len(seen)) for symbol in symbols)


def matching_starts(symbols, crib):
    if not 1 <= len(crib) <= 64:
        raise ValueError('Supply between 1 and 64 rune tokens')
    target = pattern(crib)
    return [i for i in range(max(0, len(symbols) - len(crib) + 1))
            if pattern(symbols[i:i + len(crib)]) == target]


def report(page_id, crib_text):
    index_bytes = (ROOT / 'data/index.json').read_bytes()
    index = json.loads(index_bytes)
    if page_id not in {page['id'] for page in index['pages']}:
        raise ValueError('Unknown page ID; use a release ID such as lp2-42')
    alphabet = index['alphabet']
    lookup = {a['rune']: a['index'] for a in alphabet}
    aliases = {}
    for entry in alphabet:
        for label in [entry['rune'], entry['latin'], *entry['aliases']]:
            aliases[label.upper()] = entry['index']
    labels = crib_text.upper().split()
    if not 1 <= len(labels) <= 64:
        raise ValueError('Supply between 1 and 64 rune tokens')
    unknown = [label for label in labels if label not in aliases]
    if unknown:
        raise ValueError('Unknown rune label(s): ' + ', '.join(unknown) +
                         '. Separate labels with spaces; TH is one rune.')
    crib = [aliases[label] for label in labels]
    source = ROOT / 'text' / (page_id + '.txt')
    raw = source.read_bytes()
    text = raw.decode('utf-8')
    if any('\u16a0' <= c <= '\u16ff' and c not in lookup for c in text):
        raise ValueError('Source contains a rune outside the stored alphabet')
    symbols, positions = indexed_runes(text, lookup)
    starts = matching_starts(symbols, crib)
    matches = []
    for start in starts:
        window = symbols[start:start + len(crib)]
        mapping = dict(zip(window, crib))
        matches.append({**occurrence(text, positions, start, len(crib)),
                        'cipher_indices': window,
                        'mapping': [{'cipher_index': c, 'plain_index': p}
                                    for c, p in sorted(mapping.items())]})
    return {'schema': 'liberpedia-crib-pattern-v1', 'page': page_id,
            'method': 'Fixed one-to-one substitution equality pattern; each alignment independently.',
            'boundaries': 'All archived runes including headings; separators ignored; overlapping windows; no page joins.',
            'positions': 'Zero-based rune and Unicode offsets; source_end exclusive; source line/column one-based.',
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'alphabet_index_sha256': hashlib.sha256(index_bytes).hexdigest(),
            'crib_indices': crib, 'pattern': list(pattern(crib)),
            'rune_count': len(symbols),
            'windows_checked': max(0, len(symbols) - len(crib) + 1),
            'match_count': len(matches), 'matches': matches,
            'limits': 'Compatibility only: no language score, key recovery, word-boundary test, or significance claim. Matches can require different mappings.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('page')
    parser.add_argument('--crib', required=True, help='Space-separated rune labels or rune glyphs')
    parser.add_argument('--output', type=Path, help='Save UTF-8 JSON; refuses to overwrite')
    args = parser.parse_args()
    try:
        result = report(args.page, args.crib)
        serialized = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(serialized)
            print(f"Saved {result['match_count']} compatible windows to {args.output}")
        else:
            print(serialized, end='')
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
