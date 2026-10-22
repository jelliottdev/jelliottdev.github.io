"""Independent direct scan of the saved word-internal lag-six claims."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
result = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet = json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
lookup = {row['rune']: i for i, row in enumerate(alphabet)}
inside = crossing = inside_pairs = crossing_pairs = 0
for page in range(56):
    raw = (ROOT/f'text/lp2-{page:02d}.txt').read_text(encoding='utf-8')
    # Split only on visible hyphen and full stop; ignore layout marks inside a word.
    groups = [[lookup[c] for c in segment if c in lookup]
              for segment in re.split(r'[-.]', raw)]
    stream = [(value, group) for group, values in enumerate(groups) for value in values]
    for (left, left_group), (right, right_group) in zip(stream, stream[6:]):
        equal = right == (24 - 2*left) % 29
        if left_group == right_group:
            inside_pairs += 1
            inside += equal
        else:
            crossing_pairs += 1
            crossing += equal
assert (inside, inside_pairs) == (77, 1267)
assert (crossing, crossing_pairs) == (389, 11359)
assert (inside, inside_pairs) == (result['target']['matches'], result['target']['opportunities'])
assert (crossing, crossing_pairs) == (result['crossing_word_gaps']['matches'], result['crossing_word_gaps']['opportunities'])
assert result['affine_family']['candidate_count'] == 841
assert result['affine_family']['target_rank'] == 1
print('PASS: independent rune scan, word-gap split, and saved results')
