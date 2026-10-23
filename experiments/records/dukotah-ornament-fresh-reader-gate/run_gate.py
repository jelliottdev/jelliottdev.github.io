"""Test the fresh 229-class A-06 reader on held-out solved LP2 pages."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / 'source/liber-primus'
BANK = ROOT / 'experiments/records/dukotah-t2-fresh-template-loo'
PLAN = HERE / 'variant-plan.json'
OUT = HERE / 'gate-results.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', type=Path, default=SOURCE)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    for name, expected in plan['inputs']['source'].items():
        assert sha(args.source_root / name) == expected, name
    for name, expected in plan['inputs']['local'].items():
        assert sha(ROOT / name) == expected, name

    lane = args.source_root / 'analysis/round18/L3-ornaments'
    sys.path.insert(0, str(lane))
    sys.path.insert(0, str(args.source_root / 'src'))
    import calibrate  # noqa: E402 — exact source routine
    import reader as R  # noqa: E402
    from lp.gematria import RUNE_TO_IDX  # noqa: E402

    R.RT = str(BANK)
    templates = R.load_templates()
    mapping = R.load_mapping()
    assert len(templates) == 33  # Fresh bank keeps 33 classes, not historical 32.

    rows = []
    total_match = total_cmp = 0
    all_costs = []
    for number, source_label in ((56, '73.jpg - 56.jpg'), (57, '74.jpg - 57.jpg')):
        canonical = calibrate.canon_runes(source_label)
        page = json.loads((ROOT / f'data/pages/lp2-{number:02d}.json').read_text(encoding='utf-8'))
        site = [RUNE_TO_IDX[c] for c in page['raw'] if c in RUNE_TO_IDX]
        canonical_differences = [i for i, (a, b) in enumerate(zip(site, canonical)) if a != b]
        assert len(site) == len(canonical)
        seq, costs, _, bands = calibrate.read_page(
            str(ROOT / f'images/lp2-{number:02d}.jpg'), templates, mapping, strip=True)
        matched = sum(m.size for m in difflib.SequenceMatcher(
            a=seq, b=canonical, autojunk=False).get_matching_blocks())
        site_matched = sum(m.size for m in difflib.SequenceMatcher(
            a=seq, b=site, autojunk=False).get_matching_blocks())
        compared = max(len(seq), len(canonical))
        total_match += matched
        total_cmp += compared
        all_costs.extend(costs)
        rows.append({'page': f'lp2-{number:02d}', 'image_rows': len(bands),
                     'predicted_runes': len(seq), 'canonical_runes': len(canonical),
                     'matched': matched, 'compared': compared,
                     'agreement': matched / compared,
                     'site_canonical_mismatch_positions_zero_based': canonical_differences,
                     'site_canonical_matched': site_matched,
                     'predicted_indices': seq,
                     'source_canonical_indices': canonical,
                     'site_canonical_indices': site,
                     'predicted_indices_sha256': hashlib.sha256(bytes((x + 1) % 256 for x in seq)).hexdigest()})

    result = {
        'schema': 'liberpedia-a06-fresh-reader-gate-v1',
        'variant_plan_sha256': sha(PLAN),
        'source_revision': plan['source_revision'],
        'fresh_template_classes': 229,
        'templates_kept': len(templates),
        'mapped_classes': len(mapping),
        'solved_page_controls': rows,
        'overall': {'matched': total_match, 'compared': total_cmp,
                    'agreement': total_match / total_cmp,
                    'source_gate_threshold': 0.90,
                    'pass': total_match / total_cmp >= 0.90},
        'known_text_template_cost': {
            'median': float(np.median(all_costs)),
            'p90': float(np.quantile(all_costs, 0.90)),
            'p99': float(np.quantile(all_costs, 0.99))},
        'interpretation': 'Raw template-DP page read without canonical-position assistance; fresh instrument, not a replay of the missing historical 226-class array.'
    }
    payload = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        assert OUT.read_text(encoding='utf-8') == payload
    else:
        OUT.write_text(payload, encoding='utf-8', newline='\n')
    print(json.dumps(result['overall']))


if __name__ == '__main__':
    main()
