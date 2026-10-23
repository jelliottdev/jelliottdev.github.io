"""Independent spot and census checks for the fixed header-crib experiment."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
A = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
S = {r: i for i, r in enumerate(A)}
TARGETS = {'A': 24, 'I': 10, 'O': 3}
report = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
assert report['eligible_visible_pairs'] == len(report['all_pairs']) == 13
assert len(report['target_pair']['variants']) == 6
assert report['target_pair']['cipher'] == 'ᚪᛗᛝᛞᛡᚦᛉᛁᛗ'

# Reparse every page independently rather than trusting the producer's pair list.
seen = []
rx = re.compile('[' + A + ']+')
for page in range(56):
    name = f'lp2-{page:02d}'
    tokens = rx.findall((ROOT / 'text' / (name + '.txt')).read_text(encoding='utf-8'))
    seen.extend((name, i, x + y) for i, (x, y) in enumerate(zip(tokens, tokens[1:]))
                if len(x) == 1 and len(y) == 8)
assert seen == [(c['page'], c['pair_index'], c['cipher']) for c in report['all_pairs']]

# Rebuild the eight-rune lexicon with a second CSV pass.
manifest = json.loads((ROOT / 'experiments/records/word-sum-corpus-control/source/SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
lexicon = set()
for item in manifest['files']:
    path = ROOT / 'experiments/records/word-sum-corpus-control/source' / item['path']
    for row in csv.reader(path.read_text(encoding='utf-8').splitlines()):
        glyphs = row[3].replace('ᛂ', 'ᛄ')
        if len(glyphs) == 8 and all(g in S for g in glyphs):
            lexicon.add(glyphs)
assert len(lexicon) == report['eight_rune_dictionary_spellings']

for case in report['all_pairs']:
    c = [S[x] for x in case['cipher']]
    assert len(case['variants']) == 6
    for row in case['variants']:
        p = [TARGETS[row['first']]]
        for i in range(1, 9):
            p.append((c[i] - (c[i-1] if row['mode'] == 'ciphertext' else p[-1])) % 29)
        decoded = ''.join(A[i] for i in p)
        assert decoded == row['runes']
        assert row['primer'] == (c[0] - p[0]) % 29
        assert row['second_word'] == decoded[1:]
        assert bool(row['dictionary_words']) == (decoded[1:] in lexicon)

assert report['all_pair_dictionary_hits'] == 0
assert report['pairs_with_any_hit'] == 0
assert len(report['planted_positive_controls']) == 2
for planted in report['planted_positive_controls']:
    c = [S[x] for x in planted['cipher']]
    p = [TARGETS['A']]
    for i in range(1, 9):
        p.append((c[i] - (c[i-1] if planted['mode'] == 'ciphertext' else p[-1])) % 29)
    assert ''.join(A[x] for x in p[1:]) == 'ᛗᚩᚢᚾᛏᚪᛁᚾ'
    assert (c[0] - p[0]) % 29 == planted['primer'] == 7
print('OK: independent pair inventory, lexicon, 78 outputs and two planted controls')
