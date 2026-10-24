"""Exact source score order with period-three primer offsets; no fast math."""
from pathlib import Path
import sys
import importlib.util
import hashlib
import json
import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'source/analysis/round12/C1'))
import feedback as fb
spec = importlib.util.spec_from_file_location('original_control', HERE / 'source/analysis/round12/C1/control.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def model():
    table = np.full(26**4, fb.Q.floor, dtype=np.float64)
    for gram, value in fb.Q.d.items():
        code = 0
        for letter in gram:
            code = code * 26 + ord(letter) - 65
        table[code] = value
    labels = [fb.gp.IDX_TO_TRANS[i] for i in range(29)]
    letters = np.zeros((29, 2), dtype=np.int64)
    lengths = np.array([len(label) for label in labels], dtype=np.int64)
    assert max(lengths) == 2
    for i, label in enumerate(labels):
        for j, letter in enumerate(label):
            letters[i, j] = ord(letter) - 65
    return table, letters, lengths


@njit
def zero_decode(cipher):
    plain = np.empty(len(cipher), dtype=np.int64)
    for i in range(len(cipher)):
        plain[i] = cipher[i] if i < 2 else (cipher[i] - plain[i-1] - plain[i-2]) % 29
    return plain


@njit
def shifted_plain(base, a, b):
    out = np.empty(len(base), dtype=np.uint8)
    shifts = (-a, -b, a+b)
    for i in range(len(base)):
        out[i] = (base[i] + shifts[i % 3]) % 29
    return out


@njit
def score_grid(base, table, letters, lengths):
    scores = np.empty(841, dtype=np.float64)
    for a in range(29):
        for b in range(29):
            shifts = (-a, -b, a+b)
            rolling = 0
            count = 0
            total = 0.0
            for i in range(2, len(base)):
                rune = (base[i] + shifts[i % 3]) % 29
                for j in range(lengths[rune]):
                    rolling = rolling * 26 + letters[rune, j]
                    count += 1
                    if count >= 4:
                        total += table[rolling]
                    rolling %= 26**3
            scores[a*29+b] = total / (count-3) if count > 3 else -999.0
    return scores


def witness(cipher, page, index, score):
    a, b = divmod(int(index), 29)
    plain = shifted_plain(zero_decode(np.asarray(cipher, dtype=np.int64)), a, b)
    return {'page': page, 'primer': [a, b], 'score': float(score),
            'runes': plain.tolist(), 'decoded_sha256': hashlib.sha256(bytes(plain)).hexdigest(),
            'scored_transliteration': fb.idx_to_trans(plain[2:]),
            'quadgrams': len(fb.idx_to_trans(plain[2:]))-3}


def verify_inputs():
    manifest = json.loads((HERE / 'input-manifest.json').read_bytes())
    for row in manifest['files']:
        raw = (HERE / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']


def controls_plaintexts():
    known = json.loads((HERE / 'known-readings.json').read_bytes())
    warning = next(row for row in known['controls'] if row['id'] == 'warning')['decoded_pages'][0]
    return [('source-control', control.eng_to_idx(control.PLAIN)), ('warning', warning['rune_indices'])]
