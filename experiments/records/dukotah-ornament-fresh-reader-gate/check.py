"""Recount the saved raw-reader control independently of the image routine."""

import difflib
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = HERE / 'source/liber-primus'
sys.path.insert(0, str(SRC / 'src'))
from lp import corpus  # noqa: E402
from lp.gematria import RUNE_TO_IDX  # noqa: E402
plan = json.loads((HERE / 'variant-plan.json').read_text(encoding='utf-8'))
result = json.loads((HERE / 'gate-results.json').read_text(encoding='utf-8'))
assert result['variant_plan_sha256'] == hashlib.sha256(
    (HERE / 'variant-plan.json').read_bytes()).hexdigest()
assert [x['page'] for x in result['solved_page_controls']] == ['lp2-56', 'lp2-57']
total_match = total_cmp = 0
for row in result['solved_page_controls']:
    predicted = row['predicted_indices']
    source = row['source_canonical_indices']
    site = row['site_canonical_indices']
    assert all(isinstance(x, int) and -1 <= x < 29 for x in predicted)
    assert all(isinstance(x, int) and 0 <= x < 29 for x in source + site)
    assert hashlib.sha256(bytes(x + 1 for x in predicted)).hexdigest() == row['predicted_indices_sha256']
    page_json = json.loads((ROOT / f"data/pages/{row['page']}.json").read_text(encoding='utf-8'))
    assert page_json['rune_count'] == len(site)
    assert [RUNE_TO_IDX[c] for c in page_json['raw'] if c in RUNE_TO_IDX] == site
    label = '73.jpg - 56.jpg' if row['page'] == 'lp2-56' else '74.jpg - 57.jpg'
    source_page = corpus.page_by_label(label)
    assert [RUNE_TO_IDX[c] for c in source_page['runes'] if c in RUNE_TO_IDX] == source
    assert row['site_canonical_mismatch_positions_zero_based'] == [
        i for i, (a, b) in enumerate(zip(site, source)) if a != b]
    matched = sum(block.size for block in difflib.SequenceMatcher(
        a=predicted, b=source, autojunk=False).get_matching_blocks())
    site_matched = sum(block.size for block in difflib.SequenceMatcher(
        a=predicted, b=site, autojunk=False).get_matching_blocks())
    compared = max(len(predicted), len(source))
    assert (matched, compared, site_matched) == (
        row['matched'], row['compared'], row['site_canonical_matched'])
    total_match += matched
    total_cmp += compared
assert (total_match, total_cmp) == (result['overall']['matched'], result['overall']['compared'])
assert abs(result['overall']['agreement'] - total_match / total_cmp) < 1e-12
assert result['overall']['source_gate_threshold'] == 0.90
assert result['overall']['pass'] == (total_match / total_cmp >= 0.90)
inventory = json.loads((HERE / 'source/liber-primus/'
                        'analysis/round18/L3-ornaments/inventory.json').read_text(encoding='utf-8'))
assert len(inventory) == 109 and len({r['page'] for r in inventory}) == 39
print(json.dumps({'solved_page_agreement': [r['agreement'] for r in result['solved_page_controls']],
                  'combined': result['overall']['agreement'], 'passed': result['overall']['pass'],
                  'inventory_rows': len(inventory)}))
