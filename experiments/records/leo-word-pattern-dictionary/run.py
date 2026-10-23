"""Independent replay of Leo T1 using a user-supplied pinned relikd checkout.

No upstream code or corpus text is redistributed here. Python standard library only.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
RI = {r: i for i, r in enumerate(RUNES)}
BREAKS = set('•⁘⁚⁖⁜')
SECTION_NAMES = ('0_warning', '0_welcome', '0_wisdom', '0_koan_1',
                 '0_loss_of_divinity', 'jpg107-167', 'jpg229', 'p56_an_end',
                 'p57_parable', 'p0-2', 'p3-7', 'p8-14', 'p15-22', 'p23-26',
                 'p27-32', 'p33-39', 'p40-53', 'p54-55')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(text, replace=None):
    out, cur, j = [], [], 0
    for ch in text:
        if ch in RI:
            cur.append(RI[ch] if replace is None else replace[j])
            j += 1
        elif ch in BREAKS or (ch not in '\r\n'):
            if cur:
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    return out


def indices(text):
    return [RI[ch] for ch in text if ch in RI]


def prime_stream():
    primes = []
    n = 2
    while True:
        if all(n % p for p in primes if p * p <= n):
            primes.append(n)
            yield n
        n += 1


def decoded(name, cipher):
    if name in ('0_wisdom', '0_loss_of_divinity', 'jpg229', 'p57_parable'):
        return cipher[:]
    if name == '0_warning':
        return [28 - x for x in cipher]
    if name == '0_koan_1':
        return [(31 - x) % 29 for x in cipher]
    if name in ('0_welcome', 'jpg107-167', 'p56_an_end'):
        if name == '0_welcome':
            key = [23, 10, 1, 10, 9, 10, 16, 26]  # DIVINITY in GP indices
            interrupted = {4, 5, 6, 7, 10, 11, 14, 18, 20, 21, 25}
        elif name == 'jpg107-167':
            key = [0, 10, 4, 0, 1, 19, 0, 18, 4, 18, 9, 0, 18]  # FIRFUMFERENFE
            interrupted = {2, 3}
        else:
            key = None
            interrupted = {4}
        ps = prime_stream()
        out, f_seen, kpos = [], 0, 0
        for c in cipher:
            if c == 0:
                f_seen += 1
            if c == 0 and f_seen in interrupted:
                out.append(c)
                continue
            k = key[kpos % len(key)] if key is not None else next(ps) - 1
            out.append((c - k) % 29)
            kpos += 1
        return out
    raise ValueError(name)


def delta(w):
    return tuple((b - a) % 29 for a, b in zip(w, w[1:]))


def normalized(d):
    first = next((v for v in d if v), 0)
    return tuple((v * pow(first, -1, 29)) % 29 for v in d) if first else d


def compute(root, plan):
    root = Path(root)
    wanted = plan['source_sha256']
    for rel, digest in wanted.items():
        path = root / rel
        if not path.is_file() or sha(path).lower() != digest:
            raise ValueError('missing or changed source: ' + rel)
    dictionary = root / 'data/dictionary_all-rune.txt'
    signatures, reverse_signatures = set(), set()
    for line in dictionary.open(encoding='utf-8'):
        w = indices(line)
        if len(w) >= 4:
            d = delta(w)
            signatures.add(d)
            reverse_signatures.add(d[::-1])
    affine_signatures = {normalized(d) for d in signatures}
    literal_reverse_signatures = {tuple((-x) % 29 for x in d[::-1])
                                  for d in signatures}
    cipher_words, plain_words = [], []
    section_rows = []
    for name in SECTION_NAMES:
        text = (root / 'pages' / (name + '.txt')).read_text(encoding='utf-8')
        c = indices(text)
        cw = words(text)
        section_rows.append({'section': name, 'runes': len(c), 'words': len(cw)})
        if name.startswith('p') and name != 'p56_an_end' and name != 'p57_parable':
            cipher_words.extend(cw)
        else:
            plain_words.extend(words(text, decoded(name, c)))
    if sum(r['runes'] for r in section_rows[9:]) != 12956:
        raise ValueError('unexpected unsolved source length')
    rng = random.Random(1)
    rows = []
    for length in range(4, 9):
        cw = [w for w in cipher_words if len(w) == length]
        pw = [w for w in plain_words if len(w) == length]
        rw = [[rng.randrange(29) for _ in range(length)] for _ in range(2000)]
        # Leo calls reversed difference tuples "reversed". Literal word reversal
        # negates each difference as well, so measure that separately.
        source_reverse = sum(delta(w) in reverse_signatures for w in cw)
        actual_word_reverse = sum(delta(w) in literal_reverse_signatures for w in cw)
        rows.append({
            'length': length, 'cipher_words': len(cw), 'plain_words': len(pw),
            'caesar_hits': sum(delta(w) in signatures for w in cw),
            'source_reverse_difference_hits': source_reverse,
            'literal_reverse_caesar_hits': actual_word_reverse,
            'affine_hits': sum(normalized(delta(w)) in affine_signatures for w in cw),
            'random_n': len(rw),
            'random_caesar_hits': sum(delta(w) in signatures for w in rw),
            'random_affine_hits': sum(normalized(delta(w)) in affine_signatures for w in rw),
            'solved_plain_caesar_hits': sum(delta(w) in signatures for w in pw),
        })
    return {'schema': 'leo-t1-word-pattern-v1', 'source_revision': plan['source_revision'],
            'sections': section_rows, 'signature_counts': {'caesar': len(signatures),
             'source_reverse_difference': len(reverse_signatures), 'affine': len(affine_signatures)},
            'rows': rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True, help='pinned relikd checkout')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    result = compute(args.source_root, plan)
    path = HERE / 'results.json'
    if args.check:
        if result != json.loads(path.read_text(encoding='utf-8')):
            raise SystemExit('results differ')
        print('source hashes and all results match')
    else:
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('wrote', path)


if __name__ == '__main__':
    main()
