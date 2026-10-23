"""Receipt, scope and transform checks independent of run.py."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = [
    # length, cipher words, Caesar, source-reversed differences, affine,
    # random Caesar, random affine, solved-plain Caesar numerator/denominator
    (4, 511, 165, 157, 511, 627, 1986, 131, 131),
    (5, 317, 12, 9, 166, 45, 1074, 57, 57),
    (6, 256, 0, 0, 13, 4, 93, 63, 65),
    (7, 216, 0, 0, 1, 0, 2, 46, 47),
    (8, 156, 0, 0, 0, 0, 1, 25, 25),
]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX = {c: i for i, c in enumerate(RUNES)}
BREAKS = set('•⁘⁚⁖⁜')


def anchored(word):
    """Translation-invariant offsets; independent of adjacent differences."""
    return tuple((x - word[0]) % 29 for x in word[1:])


def affine_anchor(offsets):
    first = next((x for x in offsets if x), 0)
    return tuple(x * pow(first, -1, 29) % 29 for x in offsets) if first else offsets


def word_indices(text):
    current = []
    for c in text:
        if c in INDEX:
            current.append(INDEX[c])
        elif c in BREAKS or c not in '\r\n':
            if current:
                yield tuple(current)
                current = []
    if current:
        yield tuple(current)


def independent_observed(root, plan, data):
    """Full LP2 membership census via anchored offsets, not producer deltas."""
    signatures = set()
    with (root / 'data/dictionary_all-rune.txt').open(encoding='utf-8') as f:
        for line in f:
            seq = tuple(INDEX[c] for c in line if c in INDEX)
            if len(seq) >= 4:
                signatures.add(anchored(seq))
    affine = {affine_anchor(s) for s in signatures}
    counts = {n: [0, 0, 0] for n in range(4, 9)}
    for section in data['sections'][9:]:
        path = root / 'pages' / (section['section'] + '.txt')
        for word in word_indices(path.read_text(encoding='utf-8')):
            n = len(word)
            if n in counts:
                a = anchored(word)
                counts[n][0] += 1
                counts[n][1] += a in signatures
                counts[n][2] += affine_anchor(a) in affine
    for row in data['rows']:
        assert counts[row['length']] == [row['cipher_words'], row['caesar_hits'], row['affine_hits']], row['length']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', help='optional pinned relikd checkout')
    args = ap.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert data['source_revision'] == plan['source_revision']
    assert sum(s['runes'] for s in data['sections'][9:]) == 12956
    assert len(data['sections']) == 18
    for row, exp in zip(data['rows'], EXPECTED):
        actual = tuple(row[k] for k in ('length', 'cipher_words', 'caesar_hits',
            'source_reverse_difference_hits', 'affine_hits', 'random_caesar_hits',
            'random_affine_hits', 'solved_plain_caesar_hits', 'plain_words'))
        assert actual == exp, (actual, exp)
        assert row['random_n'] == 2000
    assert len(data['rows']) == 5
    # Source's d[::-1] lacks the sign needed for literal rune-word reversal:
    # Δ(reverse(w)) = -reverse(Δ(w)) modulo 29.
    word = (1, 4, 9, 2)
    d = tuple((b - a) % 29 for a, b in zip(word, word[1:]))
    rev_d = tuple((b - a) % 29 for a, b in zip(word[::-1], word[-2::-1]))
    assert rev_d == tuple((-v) % 29 for v in d[::-1])
    assert rev_d != d[::-1]
    if args.source_root:
        root = Path(args.source_root)
        for rel, want in plan['source_sha256'].items():
            assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == want, rel
        independent_observed(root, plan, data)
    print('published counts, source receipt, anchored-offset LP2 census and reversal identity match')


if __name__ == '__main__':
    main()
