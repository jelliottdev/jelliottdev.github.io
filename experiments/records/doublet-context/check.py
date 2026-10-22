"""Independently recount doublet symbols and the differences beside them."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE / 'plan.txt').read_bytes()).hexdigest() == result['plan_sha256']
    index = (ROOT / 'data/index.json').read_bytes()
    assert hashlib.sha256(index).hexdigest() == result['input_sha256']['data/index.json']
    alphabet = json.loads(index)['alphabet']
    values = {entry['rune']: i for i, entry in enumerate(alphabet)}
    assert len(values) == 29 and alphabet[28]['latin'] == 'EA'
    symbols, before, after = Counter(), Counter(), Counter()
    events = []
    missing_before = missing_after = neighboring_zero = transitions = 0
    for number in range(56):
        path = f'text/lp2-{number:02d}.txt'
        raw = (ROOT / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == result['input_sha256'][path]
        glyphs = re.findall('[\u16a0-\u16ff]', raw.decode('utf-8'))
        assert all(glyph in values for glyph in glyphs), path
        nums = [values[glyph] for glyph in glyphs]
        changes = [(nums[i + 1] - nums[i]) % 29 for i in range(len(nums) - 1)]
        transitions += len(changes)
        for at in range(len(changes)):
            if nums[at] != nums[at + 1]:
                continue
            left = changes[at - 1] if at else None
            right = changes[at + 1] if at + 1 < len(changes) else None
            if left is None:
                missing_before += 1
            elif left == 0:
                neighboring_zero += 1
            else:
                before[left] += 1
            if right is None:
                missing_after += 1
            elif right == 0:
                neighboring_zero += 1
            else:
                after[right] += 1
            symbols[nums[at + 1]] += 1
            events.append({'page': f'lp2-{number:02d}', 'rune_index': at + 1,
                           'ciphertext_index': nums[at + 1],
                           'ciphertext_label': alphabet[nums[at + 1]]['latin'],
                           'preceding_difference': left,
                           'following_difference': right})
    observed = result['observed']
    symbol_bins = [symbols[i] for i in range(29)]
    before_bins = [before[i] for i in range(1, 29)]
    after_bins = [after[i] for i in range(1, 29)]
    assert transitions == result['within_page_transitions'] == 12901
    assert events == observed['events'] and len(events) == 86
    assert symbol_bins == observed['symbol_counts']
    assert before_bins == observed['preceding_difference_counts']
    assert after_bins == observed['following_difference_counts']
    assert missing_before == observed['missing_preceding'] == 1
    assert missing_after == observed['missing_following'] == 1
    assert neighboring_zero == observed['neighboring_zero_exclusions'] == 0
    assert sum(symbol_bins) == 86 and sum(before_bins) == sum(after_bins) == 85
    assert sum(c * (c - 1) // 2 for c in symbol_bins) == observed['collision_pairs'] == 123
    imbalance = sum((a - b) ** 2 / (a + b + 1) for a, b in zip(before_bins, after_bins))
    assert abs(imbalance - observed['context_imbalance']) < 1e-12
    assert result['reference']['positive_control'] is True
    print('PASS: independent rune extraction, 86 event ledger, neighbor bins and both diagnostics')


if __name__ == '__main__':
    main()
