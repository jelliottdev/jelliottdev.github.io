"""Build record metadata with current, declared file hashes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f'experiments/records/{HERE.name}/'


def hashed(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    d = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert (d['plain_runes'], d['lp2_runes'], d['lp2_sections'], d['lp2_pair_opportunities'], d['lp2_doublets']) == (2901, 12956, 9, 12947, 86)
    assert d['C3']['count_compatible'] == ['NG', 'IA', 'EA']
    assert d['C3']['excluded_under_source_rule'] == 29
    assert abs(d['C15']['minimum_expected_chi2'] - 4802.036755067442) < 1e-8
    assert abs(d['C15']['observed_lp2_chi2'] - 26.361685705464648) < 1e-8
    inputs = [BASE + n for n in ('plan.json', 'run.py', 'check.py', 'replay_source.py', 'plot.py', 'make_record.py', 'source-tests.txt')]
    inputs += ['data/index.json', 'data/evidence/known-readings.json']
    inputs += [f'text/lp2-{i:02d}.txt' for i in range(56)]
    record = {
        'id': HERE.name, 'status': 'draft',
        'title': 'Two letter-encoding bounds on LP2',
        'question': 'Do visible rune repeats mark one plaintext rune, or can a fixed set of dedicated homophones explain LP2 rune frequencies?',
        'reader_question': 'Could simple rules for repeated runes or homophones explain LP2?',
        'summary': 'Two source-defined rules make predictions about visible runes; neither fits under its stated assumptions.',
        'finding': 'The marker rule narrows 29 plaintext runes to NG, IA and EA by repeat count, then none survives the word-position check. In a separate fixed, even-choice homophone model, the optimal expected frequency mismatch is 4,802 versus 26 observed on LP2; the source cutoff is 200. Six targeted source tests pass and independent checks reconstruct the manuscript statistics and optimum.',
        'limitations': 'Both are conditional model exclusions, not statements about every cipher. The marker result uses solved-reading frequencies and word positions as plaintext proxies and assumes a fixed marker with nonzero multiplier. The homophone result assumes dedicated ciphertext symbols, even choices and the solved sample as a plaintext-frequency proxy. Context-dependent mappings, uneven choices and further layers are not tested.',
        'next_steps': 'Specify the mapping, reset and frequency assumptions of any related proposal, then test its complete output against manuscript and planted controls.',
        'outcome': 'not-supported',
        'tags': ['LP2', 'source replay', 'doublets', 'homophonic substitution', 'frequency analysis', 'word positions'],
        'scope': {
            'pages': [f'lp2-{i:02d}' for i in range(56)],
            'artifacts': [BASE + 'source-tests.txt'],
            'representation': 'Canonical GP29 rune indices from LP2-00–55; 2,901 solved plaintext runes for conditional frequency/position calibration. Nine LP2 section boundaries prevent a false adjacent pair.',
            'procedure': 'Replay original C3 and C15 source tests. Independently count LP2 repeats and word classes, run all 29 C3 marker candidates with the original Poisson and position cutoffs, and enumerate/verify the best C15 ciphertext-symbol allocation.',
            'parameters': 'C3: 12,947 adjacent opportunities, 86 doublets, count p<1e-6 and word-position LLR<=-10 exclusion gates. C15: 29 ciphertext symbols allocated to 26 used plaintext categories; 3,654 allocations including unused slots; even within-category choices; expected chi-square exclusion cutoff 200.',
            'exclusions': 'Other text layers, alternate word segmentation, changing marker runes, zero or adaptive multipliers, unequal or shared homophones, stateful alphabets, non-LP1 plaintext priors and additional cipher stages.'
        },
        'review': {
            'kind': 'pinned public-source targeted test replay with independent site-corpus checks',
            'retested_on': '2026-10-23',
            'reviewer': 'Six original targeted tests pass; separate site-corpus reconstruction and independent allocation dynamic program reproduce decisive values',
            'human_review': 'pending'
        },
        'reproduction': {
            'command': f'python {BASE}check.py && python {BASE}plot.py --check',
            'environment': 'Python 3 standard library for bundled checks; original tests additionally require the pinned external Wulfic checkout.',
            'script': BASE + 'check.py', 'script_sha256': hashed(BASE + 'check.py')['sha256'],
            'inputs': [hashed(p) for p in inputs],
            'outputs': [hashed(BASE + n) for n in ('results.json', 'comparison.svg')]
        },
        'visuals': [{'path': BASE + 'comparison.svg', 'caption': 'Two conditional tests: the fixed marker candidate funnel and the expected-versus-observed rune-frequency contrast.'}],
        'sources': [
            {'label': 'Pinned marker-letter test', 'url': 'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests/test_leak.py'},
            {'label': 'Pinned homophonic-frequency test', 'url': 'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests/test_stats.py'}
        ],
        'related': ['doublet-context', 'ea-frequency-control', 'wulfic-position-alphabet-flatness-bound']
    }
    (HERE / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
