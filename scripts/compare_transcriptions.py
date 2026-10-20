"""Compare two UTF-8 transcriptions without modifying either input.

Usage: python scripts/compare_transcriptions.py old.txt new.txt
Output: JSON on stdout. Differences are data, not a failing exit status.
Invalid UTF-8 or unknown Runic-block characters fail rather than disappearing.
Requires data/index.json alongside scripts/, as supplied in the reference ZIP.
"""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_input(path, alphabet):
    raw = Path(path).read_bytes()
    text = raw.decode('utf-8')  # Preserve BOM and CRLF in the exact-text view.
    unknown = sorted({c for c in text if '\u16a0' <= c <= '\u16ff'
                      and c not in alphabet})
    if unknown:
        raise ValueError('Unrecognized Runic-block character(s): ' +
                         ', '.join(f'U+{ord(c):04X}' for c in unknown))
    positions = []
    runes = []
    line, column = 1, 1
    for offset, char in enumerate(text):
        if char in alphabet:
            positions.append({'source_offset': offset, 'line': line,
                              'column': column})
            runes.append(char)
        if char == '\n':
            line, column = line + 1, 1
        else:
            column += 1
    return raw, text, ''.join(runes), positions


def changes(left, right, left_positions=None, right_positions=None):
    result = []
    for kind, i, j, k, l in SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if kind == 'equal':
            continue
        item = {'operation': kind, 'left_range': [i, j], 'right_range': [k, l],
                'left_text': left[i:j], 'right_text': right[k:l]}
        if left_positions is not None:
            item['left_positions'] = left_positions[i:j]
            item['right_positions'] = right_positions[k:l]
        result.append(item)
    return result


def compare(left_path, right_path, alphabet):
    left = read_input(left_path, alphabet)
    right = read_input(right_path, alphabet)
    records = []
    for path, (raw, text, runes, positions) in zip([left_path, right_path], [left, right]):
        records.append({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                        'bytes': len(raw), 'characters': len(text), 'runes': len(runes),
                        'rune_sha256': hashlib.sha256(runes.encode('utf-8')).hexdigest(),
                        'non_rune_counts': dict(sorted(Counter(c for c in text if c not in alphabet).items()))})
    return {'schema': 'liberpedia-transcription-comparison-v1',
            'scope': 'Exact decoded text and the ordered 29-symbol rune stream; no normalization.',
            'coordinates': 'Ranges and source offsets are zero-based Unicode code-point positions, end-exclusive. Lines and columns are one-based; LF starts a new physical text-file line. Rune ranges count only recognized runes.',
            'alignment': 'SequenceMatcher with autojunk disabled; repeated text can have multiple plausible alignments. This is not a manual image verification.',
            'alphabet': ''.join(alphabet), 'inputs': records,
            'bytes_equal': left[0] == right[0], 'runes_equal': left[2] == right[2],
            'text_changes': changes(left[1], right[1]),
            'rune_changes': changes(left[2], right[2], left[3], right[3])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left', type=Path)
    parser.add_argument('right', type=Path)
    args = parser.parse_args()
    try:
        alphabet = [a['rune'] for a in json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']]
        if len(alphabet) != 29 or len(set(alphabet)) != 29:
            raise ValueError('Expected 29 distinct alphabet runes')
        report = compare(args.left, args.right, alphabet)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f'Cannot compare: {exc}\n')
    # ASCII escapes keep JSON portable across terminal encodings.
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
