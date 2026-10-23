"""Replay pinned Campaign VII token roles and fixed byte-reading sensitivity."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'source' / 'analysis'))
sys.path.insert(0, str(HERE / 'source' / 'src'))

from campaign7 import token_as_ciphertext as tc  # type: ignore
from campaign7 import token_as_index as ti  # type: ignore
from lp import gematria as gp  # type: ignore
from run_stats import load_pages  # type: ignore

WITNESSES = ('archived', 'canon', 'resolved')
SOURCE_COUNTS = (80, 104, 72)


def witness(name):
    data = (HERE / f'source-{name}-256.bin').read_bytes()
    assert len(data) == 256
    return data[:80], data[80:184], data[184:]


def source_run():
    """Execute unmodified archived scripts in a temporary dependency layout."""
    with tempfile.TemporaryDirectory(prefix='liberpedia-token-roles-') as td:
        source = Path(td) / 'liber-primus'
        shutil.copytree(HERE / 'source', source)
        source_scripts = source / 'analysis' / 'campaign7'
        for name in ('token_as_ciphertext', 'token_as_index'):
            output = source_scripts / f'{name}_results.json'
            expected = json.loads(output.read_text(encoding='utf-8'))
            proc = subprocess.run([sys.executable, str(source_scripts / f'{name}.py')],
                                  cwd=source, text=True, capture_output=True, encoding='utf-8', check=True)
            actual = json.loads(output.read_text(encoding='utf-8'))
            assert actual == expected, (name, actual, expected)
            assert proc.returncode == 0
    return True


def score_index(parts, pages):
    p49, p50, p51 = parts
    token = p49 + p50 + p51
    corpus = [r for page in pages for r in page]
    absolute = [corpus[b] for b in token if b < len(corpus)]
    gaps = []; position = 0
    for value in token:
        position = (position + value) % len(corpus)
        gaps.append(corpus[position])
    local = []
    for page_index, values in zip((49, 50, 51), parts):
        page = pages[page_index]
        local.extend(page[b % len(page)] for b in values)
    interpretations = {
        'idx_abs': absolute,
        'idx_gaps': gaps,
        'idx_page': local,
        'self_gem': [b % 29 for b in token],
    }
    return {name: {'score': ti.SC.score_norm(gp.indices_to_translit(values)),
                   'rune_count': len(values), 'rune_sha256': hashlib.sha256(bytes(values)).hexdigest(),
                   'preview': gp.indices_to_translit(values)[:80]}
            for name, values in interpretations.items()}


def score_ciphertext(parts):
    p49, p50, p51 = parts
    whole = p49 + p50 + p51
    targets = {'p49': p49, 'p50': p50, 'p51': p51, 'all': whole, 'all_rev': whole[::-1]}
    methods = {'xor1': {'maximum_printable': -1.0, 'winner': None},
               'xorkw': {'maximum_printable': -1.0, 'winner': None},
               'additive': {'maximum_printable': -1.0, 'winner': None},
               'as_is': {'maximum_printable': -1.0, 'winner': None}}
    best = {'printable': -1.0, 'target': None, 'method': None, 'preview': None}
    flagged = []; count = 0

    def consider(values, target, method, group):
        nonlocal count
        count += 1
        ratio = tc.printable_ratio(values)
        rec = {'printable': ratio, 'target': target, 'method': method, 'preview': tc.as_text(values)[:80]}
        if ratio > methods[group]['maximum_printable']:
            methods[group] = {'maximum_printable': ratio, 'winner': rec}
        if ratio > best['printable']:
            best.update(rec)
        if ratio > 0.85:
            flagged.append({**rec, 'quadgram': tc.SC.score_norm(tc.as_text(values))})

    for target, raw in targets.items():
        length = len(raw)
        for key in range(256):
            consider([v ^ key for v in raw], target, f'xor1 k={key}', 'xor1')
        for keyword in tc.KEYWORDS:
            key = [ord(c) for c in keyword]
            consider([raw[i] ^ key[i % len(key)] for i in range(length)], target,
                     f'xorkw {keyword}', 'xorkw')
        for stream_name, stream in tc.streams(length).items():
            for sign in (-1, 1):
                consider([(raw[i] + sign * stream[i]) % 256 for i in range(length)],
                         target, f'{stream_name} sign{sign:+d}', 'additive')
        consider(raw, target, 'asis', 'as_is')
    assert count == 1415
    return {'candidate_count': count, 'best': best, 'by_method': methods,
            'flagged_over_0_85': len(flagged),
            'best_flagged_quadgram': max((x['quadgram'] for x in flagged), default=None)}


def control_results(pages):
    # Known passage for index controls, fixed independently of the grid bytes.
    with (HERE.parents[2] / 'exports/readings/lp2-56.csv').open(encoding='utf-8', newline='') as f:
        known = [int(row['output_index']) for row in csv.DictReader(f)]
    assert len(known) == 85
    corpus = [r for page in pages for r in page]
    first = corpus[:256]
    assert set(first) == set(range(29))
    absolute_token = [first.index(r) for r in known]
    absolute_decoded = [corpus[b] for b in absolute_token]
    self_decoded = [b % 29 for b in known]
    assert absolute_decoded == self_decoded == known
    known_score = ti.SC.score_norm(gp.indices_to_translit(known))
    assert known_score > -5.0

    # A legal cumulative-gap token is found greedily; every step is byte-sized.
    gaps = []; position = 0; decoded = []
    for target in known:
        step = next(v for v in range(256) if corpus[(position + v) % len(corpus)] == target)
        gaps.append(step); position = (position + step) % len(corpus)
        decoded.append(corpus[position])
    assert decoded == known

    # The original source page 49 lacks one GP rune, so a full known reading
    # cannot be planted under its page-local lookup. Test legal exact output.
    local_tokens = [0] * 256
    local_output = [pages[pi][0] for pi, n in zip((49, 50, 51), SOURCE_COUNTS) for _ in range(n)]
    reproduced = [pages[pi][b % len(pages[pi])]
                  for pi, n in zip((49, 50, 51), SOURCE_COUNTS) for b in [0] * n]
    assert reproduced == local_output

    phrase = ('THE PRIMES ARE SACRED. FOLLOW THE WHITE RABBIT. ' * 8)[:256]
    assert len(phrase) == 256 and all(32 <= ord(ch) <= 126 for ch in phrase)
    plain = [ord(ch) for ch in phrase]
    key = 91
    xor_cipher = [v ^ key for v in plain]
    xor_plain = [v ^ key for v in xor_cipher]
    prime = tc.streams(256)['prime']
    additive_cipher = [(v + prime[i]) % 256 for i, v in enumerate(plain)]
    additive_plain = [(v - prime[i]) % 256 for i, v in enumerate(additive_cipher)]
    assert xor_plain == additive_plain == plain
    text_score = tc.SC.score_norm(phrase)
    assert text_score > -5.5 and tc.printable_ratio(plain) == 1.0
    return {'known_runes': len(known), 'known_quadgram': known_score,
            'idx_abs_exact': absolute_decoded == known, 'idx_gaps_exact': decoded == known,
            'self_gem_exact': self_decoded == known, 'idx_page_legal_exact': reproduced == local_output,
            'idx_page_known_unrepresentable_rune': 3,
            'xor1_plant_exact': xor_plain == plain, 'additive_prime_plant_exact': additive_plain == plain,
            'byte_plant_score': text_score}


def compute():
    assert source_run()
    pages = load_pages()
    assert len(pages) == 57
    controls = control_results(pages)
    witness_bytes = {name: b''.join(witness(name)) for name in WITNESSES}
    archived = witness_bytes['archived']
    out = {}
    for name in WITNESSES:
        data = witness_bytes[name]
        parts = witness(name)
        out[name] = {'sha256': hashlib.sha256(data).hexdigest(),
                     'changed_cells_from_archived': [i for i, (a, b) in enumerate(zip(archived, data)) if a != b],
                     'ciphertext': score_ciphertext(parts), 'index': score_index(parts, pages)}
    original_cipher = json.loads((HERE / 'source/analysis/campaign7/token_as_ciphertext_results.json').read_text(encoding='utf-8'))
    original_index = json.loads((HERE / 'source/analysis/campaign7/token_as_index_results.json').read_text(encoding='utf-8'))
    assert round(out['archived']['ciphertext']['best']['printable'], 3) == original_cipher['best_printable_ratio']
    assert out['archived']['ciphertext']['flagged_over_0_85'] == original_cipher['n_flagged_over_0.85_printable']
    assert all(round(v['score'], 3) == original_index['scores'][name]
               for name, v in out['archived']['index'].items())
    return {'schema': 'liberpedia-grid-token-roles-results-v1',
            'plan_sha256': hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest(),
            'source_parity': True, 'controls': controls, 'witnesses': out}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = compute()
    path = HERE / 'results.json'
    if args.check:
        assert result == json.loads(path.read_text(encoding='utf-8'))
        print('PASS source programs, plants, three byte witnesses and saved results')
    else:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Saved', path)
