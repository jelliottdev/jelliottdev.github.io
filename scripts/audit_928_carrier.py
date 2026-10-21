"""Inventory a proposed three-group carrier; no grille or chance model.

Retain headings. Remove slash/newline wraps, keep internal apostrophes,
and treat all other non-runes as word boundaries. Never merge groups.
Two independent token scanners must agree on every span.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
GROUPS = [('mayfly', 23, 26), ('wing-and-tree', 27, 32), ('cuneiform', 33, 39)]


def scan(text):
    spans = []
    i = 0
    while i < len(text):
        if text[i] not in RUNES:
            i += 1
            continue
        start = i
        i += 1
        while i < len(text):
            if text[i] in RUNES:
                i += 1
            elif text[i] == "'" and i + 1 < len(text) and text[i + 1] in RUNES:
                i += 2
            else:
                break
        spans.append((start, i))
    return spans


def calculate():
    words, groups, decimals, hashes = [], [], [], {}
    for group, first, last in GROUPS:
        chars, locations = [], []
        for number in range(first, last + 1):
            page = f'lp2-{number:02}'
            path = f'text/{page}.txt'
            raw = (ROOT / path).read_bytes()
            hashes[path] = hashlib.sha256(raw).hexdigest()
            text = raw.decode('utf-8')
            assert not any('\u16a0' <= c <= '\u16ff' and c not in RUNES for c in text)
            for match in re.finditer(r'[0-9]+', text):
                decimals.append({'page': page, 'value': match.group(), 'source_offset': match.start(),
                                 'line': text.count('\n', 0, match.start()) + 1})
            line = 1
            for offset, char in enumerate(text):
                if char not in '/\r\n':
                    chars.append(char)
                    locations.append({'page': page, 'line': line, 'source_offset': offset})
                if char == '\n':
                    line += 1
        joined = ''.join(chars)
        spans = scan(joined)
        regex_spans = [m.span() for m in re.finditer(f"[{RUNES}]+(?:'[{RUNES}]+)*", joined)]
        assert spans == regex_spans
        before = len(words)
        for start, stop in spans:
            word = joined[start:stop]
            words.append({'ordinal': len(words) + 1, 'group': group, 'runes': word,
                          'rune_length': sum(c in RUNES for c in word),
                          'first': locations[start], 'last': locations[stop - 1]})
        rune_count = sum(c in RUNES for c in joined)
        assert sum(w['rune_length'] for w in words[before:]) == rune_count
        groups.append({'id': group, 'pages': [f'lp2-{n:02}' for n in range(first, last + 1)],
                       'words': len(words) - before, 'runes': rune_count})
    midpoint = len(words) // 2
    left, right = words[midpoint - 1], words[midpoint]
    separator = None
    if left['last']['page'] == right['first']['page']:
        source = (ROOT / 'text' / (left['last']['page'] + '.txt')).read_bytes().decode('utf-8')
        separator = source[left['last']['source_offset'] + 1:right['first']['source_offset']]
    return {'scope': __doc__, 'groups': groups, 'total_words': len(words),
            'total_runes': sum(g['runes'] for g in groups), 'decimal_tokens': decimals,
            'halfway': {'left': left, 'right': right, 'raw_separator': separator},
            'words': words, 'source_sha256': hashes,
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limits': 'Transcription-based descriptive inventory. No image certification, grille operation, significance test or inferred authorial intent.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = calculate()
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['words', 'source_sha256', 'scope']}, ensure_ascii=True, indent=2))
