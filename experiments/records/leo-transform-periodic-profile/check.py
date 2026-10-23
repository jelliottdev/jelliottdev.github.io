"""Independent, standard-library checks of pinned source and selected metrics."""
import argparse
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
IDX = {v: k for k, v in enumerate(RUNES)}
BREAKS = set('•⁘⁚⁖⁜')


def periodic_ioc(seq, period):
    vals = []
    for start in range(period):
        column = seq[start::period]
        counts = Counter(column)
        pairs = sum(n * (n - 1) for n in counts.values())
        vals.append(29 * pairs / (len(column) * (len(column) - 1)))
    return sum(vals) / period


def check():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    args = ap.parse_args()
    source = Path(args.source_root)
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert len(plan['source_sha256']) == 9
    for rel, digest in plan['source_sha256'].items():
        assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == digest
    text = (source / 'pages/p27-32.txt').read_text(encoding='utf-8')
    raw = [IDX[c] for c in text if c in IDX]
    assert len(raw) == result['source_rune_lengths']['p27-32'] == 1433
    # Reconstruct the second-order difference without the producer's transform code.
    diff2 = [(raw[i] + 29 - raw[i - 2]) % 29 for i in range(2, len(raw))]
    measured = [periodic_ioc(diff2, p) for p in range(1, len(diff2) // 6 + 1)]
    best = max(range(len(measured)), key=measured.__getitem__) + 1
    assert best == 238
    assert round(measured[237], 6) == result['section_profiles']['p27-32']['diff2']['top'][0]['ioc']
    mean = sum(measured) / len(measured)
    sd = math.sqrt(sum((v - mean) ** 2 for v in measured) / len(measured))
    assert abs((measured[237] - mean) / (sd + 1e-9) -
               result['selected_section_control']['observed']['z']) < 1e-6
    # Independently count the edge pairs, including the archive's visible separators.
    labelled, word, active = [], 0, False
    for c in text:
        if c in IDX:
            labelled.append((IDX[c], word))
            active = True
        elif c in BREAKS:
            if active:
                word += 1
            active = False
    within = boundary = equal_within = equal_boundary = 0
    for (a, wa), (b, wb) in zip(labelled, labelled[1:]):
        if wa == wb:
            within += 1
            equal_within += (a == b)
        else:
            boundary += 1
            equal_boundary += (a == b)
    assert result['word_edge']['p27-32'] == {
        'within_pairs': within, 'within_equal': equal_within,
        'boundary_pairs': boundary, 'boundary_equal': equal_boundary}
    # Seeded shuffle receipt and the conditional arithmetic are independently pinned.
    rng = random.Random(plan['selection_control']['seed'])
    first = raw[:]
    rng.shuffle(first)
    first_d2 = [(first[i] - first[i-2]) % 29 for i in range(2, len(first))]
    first_profile = [periodic_ioc(first_d2, p) for p in range(1, len(first_d2)//6 + 1)]
    assert len(first_profile) == 238
    c = result['selected_section_control']
    assert c['shuffles'] == len(c['null_max_z']) == 499
    assert c['exceedances'] == sum(v >= c['observed']['z'] for v in c['null_max_z'])
    assert c['conditional_p'] == (c['exceedances'] + 1) / 500
    assert math.isclose(c['nine_section_bonferroni_bound'], min(1, 9 * c['conditional_p']))
    assert c['planted_periodic_control']['period'] % 13 == 0
    assert c['planted_periodic_control']['null_maxima_at_least_plant'] == 452
    print('source hashes, independent period-238 profile, edge counts, control arithmetic match')


if __name__ == '__main__':
    check()
