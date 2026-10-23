"""Independent recount and planted-message audit for the pinned B-12 replay."""

import argparse
import hashlib
import json
import pathlib

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
PLAN = HERE / 'source-replay-plan.json'
RESULTS = HERE / 'results.json'
GEOM = HERE / 'source-linegeom.json'
TESTS = HERE / 'source-linetests.json'
AUDIT = HERE / 'independent-controls.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text_from_bits(bits, width):
    out = []
    for start in range(0, len(bits) - width + 1, width):
        value = int(''.join(str(x) for x in bits[start:start + width]), 2)
        if width == 8:
            out.append(chr(value) if 32 <= value < 127 else '.')
        else:
            out.append('ABCDEFGHIJKLMNOPQRSTUVWXYZ.,?!'[value % 30])
    return ''.join(out)

def best_score(bits):
    grams = ('THAT','THER','WITH','TION','HERE','OULD','IGHT','HAVE','HICH',
             'WHIC','THIS','THIN','THEY','ATIO','EVER','FROM','OUGH','WERE',
             'HING','MENT','PRIM','SACR','CICA','INST')
    return max(sum(text_from_bits(ordered[phase:], width).upper().count(g) for g in grams)
               for ordered in (bits, bits[::-1]) for width in (5, 8)
               for phase in range(8))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    result = json.loads(RESULTS.read_text(encoding='utf-8'))
    geom = json.loads(GEOM.read_text(encoding='utf-8'))
    tests = json.loads(TESTS.read_text(encoding='utf-8'))
    assert result['plan_sha256'] == sha(PLAN)
    assert result['source_outputs'] == {'linegeom': sha(GEOM), 'linetests': sha(TESTS)}
    assert all(v['nonfloat_differences'] == 0 and v['within_1e_10']
               for v in result['source_archived_comparison'].values())
    rows = geom['rows']
    assert len(rows) == result['image_rows'] == 616
    assert len(geom['pages']) == 56
    assert [sum(row['page'] == p for row in rows) for p in range(56)] == result['per_page_row_counts']
    for key, g in geom['bimodality'].items():
        if g is not None:
            assert g['pass'] == (g['sep_sigma'] >= 2 and g['delta_bic'] > 10)
            assert g['pass'] == result['channels'][key]['pass']

    n_canon = sum(s['n_lines'] for s in geom['canon_segments'])
    channels = [
        [r['fill'] for r in rows], [r['left_margin'] for r in rows],
        [r['right_margin'] for r in rows], [r['y1'] - r['y0'] for r in rows],
        [r['n_body'] for r in rows], [r['n_sep'] for r in rows],
        [n for s in geom['canon_segments'] for n in s['line_runes']],
        [n for s in geom['canon_segments'] for n in s['line_words']],
    ]
    assert len(channels) == len(tests['bit_decode']) == 8
    assert [len(c) for c in channels] == [616] * 6 + [n_canon] * 2
    for vals, (_, source) in zip(channels, tests['bit_decode'].items()):
        bits = (np.asarray(vals, dtype=float) > np.median(vals)).astype(int).tolist()
        assert best_score(bits) == source['best_score'] == 0

    # Reconstruct the source's seeded draws without importing its functions.
    rng = np.random.default_rng(3301)
    for values in channels:
        for _ in range(2000):
            rng.permutation(np.arange(len(values)))
    fill = np.asarray(channels[0], dtype=float)
    noise = float(fill.std())
    planted_message = np.array([int(bit) for char in 'CICADA33'
                                for bit in format(ord(char), '08b')])
    c3a = []
    for k, source_trial in zip((0.5, 1, 2, 3, 4, 6, 8), tests['control_C3']['trials']):
        planted = fill.copy()
        planted[:64] = fill.mean() + planted_message * (k * noise) + rng.normal(0, noise, 64)
        recovered = (planted[:64] > np.median(planted[:64])).astype(int)
        matches = int(np.sum(recovered == planted_message))
        assert source_trial['k_sd'] == k
        assert round(matches / 64, 4) == source_trial['bit_recovery']
        c3a.append({'separation_sd': k, 'matching_bits': matches, 'of': 64,
                    'recovery': matches / 64})

    plain = ('THEPRIMESARESACREDTHATTHEREISNOTHINGWITHINWHICHTHEYWERE'
             'THEREFORETHISWASTHEIRONLYPATHFROM')
    unit = np.array([int(bit) for char in plain for bit in format(ord(char), '08b')])
    message_bits = np.tile(unit, len(fill) // len(unit) + 1)[:len(fill)]
    channel = message_bits + rng.normal(0, 0.05, len(fill))
    decoded_bits = (channel > np.median(channel)).astype(int)
    bit_matches = int(np.sum(decoded_bits == message_bits))
    decoded_text = text_from_bits(decoded_bits.tolist(), 8)
    intended_text = (plain * (len(fill) // len(unit) + 1))[:len(decoded_text)]
    char_matches = sum(a == b for a, b in zip(decoded_text, intended_text))
    source_control = tests['control_C3']['decoder_validation']
    assert decoded_text == source_control['text']
    assert source_control['verdict'] == 'PASS'

    independent = {
        'schema': 'liberpedia-b12-independent-controls-v1',
        'source_linegeom_sha256': sha(GEOM), 'source_linetests_sha256': sha(TESTS),
        'image_rows': len(rows), 'canonical_lines': n_canon,
        'bimodal_channels': [k for k, v in geom['bimodality'].items() if v and v['pass']],
        'source_bit_scan_scores': {k: v['best_score'] for k, v in tests['bit_decode'].items()},
        'C3a': c3a,
        'C3a_required_recovery': 0.95,
        'C3a_highest_recovery': max(row['recovery'] for row in c3a),
        'C3a_gate_pass': any(row['recovery'] >= 0.95 and
                             tests['control_C3']['trials'][i]['gmm_sep_sigma'] >= 2
                             for i, row in enumerate(c3a)),
        'C3b': {'bit_matches': bit_matches, 'bits': len(fill),
                'bit_recovery': bit_matches / len(fill),
                'character_matches': char_matches, 'characters': len(decoded_text),
                'decoded_prefix': decoded_text[:48], 'intended_prefix': intended_text[:48],
                'source_fourgram_gate': source_control['verdict'],
                'planted_message_recovered': decoded_text == intended_text},
        'interpretation': 'The source fourgram PASS does not demonstrate recovery of its planted ASCII message; its 95% bit-recovery gate also fails.'
    }
    payload = json.dumps(independent, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        assert AUDIT.read_text(encoding='utf-8') == payload
    else:
        AUDIT.write_text(payload, encoding='utf-8', newline='\n')
    print(json.dumps({'rows': len(rows), 'C3a_highest': independent['C3a_highest_recovery'],
                      'C3b_bit_recovery': independent['C3b']['bit_recovery'],
                      'C3b_char_matches': char_matches, 'of': len(decoded_text)}))

if __name__ == '__main__':
    main()
