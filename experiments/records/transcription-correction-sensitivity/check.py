"""Independent correction and rune-token checks; standard library only."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
IDS = ('lp1-10', 'lp2-05', 'lp2-07', 'lp2-11', 'lp2-15', 'lp2-35', 'lp2-37', 'lp2-38')


def rune_tokens(text, alphabet):
    text = text.replace('/', '').replace('\r', '').replace('\n', '')
    out, current = [], []
    for i, char in enumerate(text):
        if char in alphabet:
            current.append(char)
        elif char == "'" and current and i + 1 < len(text) and text[i+1] in alphabet:
            continue
        elif current:
            out.append(''.join(current))
            current = []
    if current:
        out.append(''.join(current))
    return out


def check():
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    alphabet = {a['rune'] for a in json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']}
    rows = {row['page']: row for row in saved['pages']}
    assert set(rows) == set(IDS)
    for page_id in IDS:
        page = json.loads((ROOT / 'data/pages' / (page_id+'.json')).read_text(encoding='utf-8'))
        raw, reviewed = page['raw'], page['reviewed_text']
        if page_id != 'lp1-10':
            reconstructed = raw
            for change in sorted(page['corrections'], key=lambda c:c['start'], reverse=True):
                a,b = change['start'],change['end']
                assert raw[a:b] == change['old']
                reconstructed = reconstructed[:a]+change['new']+reconstructed[b:]
            assert reconstructed == reviewed, page_id
            assert rune_tokens(raw, alphabet) == rune_tokens(reviewed, alphabet), page_id
            assert rows[page_id]['rune_token_sequence_equal']
            assert rows[page_id]['ordered_bigram_types_changed'] == 0
        else:
            left = [c for c in raw if c in alphabet]
            right = [c for c in reviewed if c in alphabet]
            assert len(left) == len(right) and Counter(left) == Counter(right)
            assert left[:116] == right[:116] and left[118:] == right[118:]
            assert left[116:118] == right[116:118][::-1]
            assert [len(t) for t in rune_tokens(raw, alphabet)] == [len(t) for t in rune_tokens(reviewed, alphabet)]
    lp2 = {}
    for mode in ('archived', 'reviewed'):
        joined = ''.join((lambda page: page['reviewed_text'] if mode == 'reviewed' and page['reviewed_text'] is not None else page['raw'])(json.loads((ROOT / 'data/pages' / f'lp2-{n:02d}.json').read_text(encoding='utf-8'))) for n in range(56))
        lp2[mode] = rune_tokens(joined, alphabet)
    assert lp2['archived'] == lp2['reviewed'] and len(lp2['archived']) == 2896
    assert saved['lp2_corpus']['archived']['token_count'] == len(lp2['archived'])
    assert saved['lp2_corpus']['reviewed']['token_count'] == len(lp2['reviewed'])
    print('PASS: all reviewed strings reconstruct; independent rune-token scan agrees')


if __name__ == '__main__':
    check()
