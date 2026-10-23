"""Independently reconstruct Wulfic's two simple letter-encoding bounds from Liberpedia data."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from itertools import combinations_with_replacement
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BREAKS = "-.,;:!?&$§"
WORD_CLASSES = ("initial", "medial", "final", "sole")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def word_class(i: int, size: int) -> str:
    if size == 1:
        return "sole"
    if i == 0:
        return "initial"
    if i == size - 1:
        return "final"
    return "medial"


def site_inputs():
    index_raw = (ROOT / "data/index.json").read_bytes()
    readings_raw = (ROOT / "data/evidence/known-readings.json").read_bytes()
    alphabet = json.loads(index_raw)["alphabet"]
    labels = [entry["latin"] for entry in alphabet]
    lookup = {entry["rune"]: i for i, entry in enumerate(alphabet)}
    assert len(labels) == len(lookup) == 29
    hashes = {"data/index.json": sha(index_raw),
              "data/evidence/known-readings.json": sha(readings_raw)}

    # The literal GP labels and decoded numeric stream must agree rune by rune.
    # Page and line wraps do not end a word; punctuation in BREAKS does.
    plain_words = []
    for control in json.loads(readings_raw)["controls"]:
        control_words = []
        word = []
        for page in control["decoded_pages"]:
            text = page["literal_transliteration"]
            indices = page["rune_indices"]
            i = j = 0
            while i < len(text):
                ch = text[i]
                if ch in BREAKS:
                    if word:
                        control_words.append(tuple(word))
                        word = []
                    i += 1
                elif ch.isupper():
                    if j >= len(indices):
                        raise AssertionError((page["page"], "extra GP label", i))
                    label = labels[indices[j]]
                    if not text.startswith(label, i):
                        raise AssertionError((page["page"], "GP label mismatch", i, label))
                    word.append(indices[j])
                    i += len(label)
                    j += 1
                elif ch in "/\n\r \t\"'()[]“”‘’" or ch.isdigit() or ch.islower():
                    i += 1
                else:
                    raise AssertionError((page["page"], "unknown literal character", ch))
            if j != len(indices):
                raise AssertionError((page["page"], "unconsumed numeric runes", j, len(indices)))
        if word:
            control_words.append(tuple(word))
        if control["id"] == "some-wisdom":
            # The following 76 runes belong to the square, not the known prose.
            if sum(map(len, control_words[:18])) != 81:
                raise AssertionError("unexpected Some Wisdom prose/square boundary")
            control_words = control_words[:18]
        plain_words.extend(control_words)

    sections = []
    current_section = []
    word = []
    for page_number in range(56):
        path = f"text/lp2-{page_number:02d}.txt"
        raw = (ROOT / path).read_bytes()
        hashes[path] = sha(raw)
        text = raw.decode("utf-8")
        unknown = {ch for ch in text if '\u16a0' <= ch <= '\u16ff' and ch not in lookup}
        if unknown:
            raise ValueError((path, unknown))
        for ch in text:
            if ch in lookup:
                word.append(lookup[ch])
            elif ch in BREAKS:
                if word:
                    current_section.append(tuple(word))
                    word = []
                if ch == "$":
                    if current_section:
                        sections.append(current_section)
                        current_section = []
            elif ch in "/\n\r \t\"'()[]“”‘’" or ch.isdigit() or (ch.isascii() and ch.isalpha()):
                continue
            else:
                raise AssertionError((path, "unknown text character", ch))
    if word:
        current_section.append(tuple(word))
    if current_section:
        sections.append(current_section)
    return labels, plain_words, sections, hashes


def poisson_pmf(k: int, lam: float) -> float:
    if lam == 0:
        return float(k == 0)
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def poisson_two_tail(k: int, lam: float) -> float:
    if lam == 0:
        return 0.0 if k else 1.0
    lower = math.fsum(poisson_pmf(j, lam) for j in range(k + 1))
    if lam >= k:
        upper = max(0.0, 1.0 - math.fsum(poisson_pmf(j, lam) for j in range(k)))
    else:
        terms = []
        j = k
        term = poisson_pmf(j, lam)
        while term > 1e-300 and (j < k + 10 or term > sum(terms) * 1e-17):
            terms.append(term)
            j += 1
            term *= lam / j
        upper = math.fsum(terms)
    return min(1.0, 2.0 * min(lower, upper))


def marker_llr(classes, words, letter, pseudo=10.0):
    counts = {c: [0] * 29 for c in WORD_CLASSES}
    for w in words:
        for i, rune in enumerate(w):
            counts[word_class(i, len(w))][rune] += 1
    total = sum(sum(v) for v in counts.values())
    frequency = sum(v[letter] for v in counts.values()) / total
    if frequency == 0:
        return None
    return math.fsum(
        math.log((counts[c][letter] + pseudo * frequency) /
                 (sum(counts[c]) + pseudo) / frequency)
        for c in classes
    )


def homophonic_min_chi2(q, n):
    used = [i for i, rate in enumerate(q) if rate > 0]
    spare = 29 - len(used)
    expected = n / 29
    best = (math.inf, None)
    for extras in combinations_with_replacement(range(len(used) + 1), spare):
        alloc = [1 + extras.count(i) for i in range(len(used))]
        unused = extras.count(len(used))
        score = unused * expected
        score += math.fsum(
            count * (n * q[letter] / count - expected) ** 2 / expected
            for letter, count in zip(used, alloc)
        )
        if score < best[0]:
            expanded = [0] * 29
            for letter, count in zip(used, alloc):
                expanded[letter] = count
            best = score, expanded
    return best


def report():
    labels, plain_words, sections, hashes = site_inputs()
    plain = [r for w in plain_words for r in w]
    cipher = [r for sec in sections for w in sec for r in w]
    pairs = sum(sum(map(len, sec)) - 1 for sec in sections)
    classes = []
    for sec in sections:
        cells = [(r, word_class(i, len(w))) for w in sec for i, r in enumerate(w)]
        classes += [cls for (left, _), (right, cls) in zip(cells, cells[1:]) if left == right]
    if (len(plain), len(cipher), len(sections), pairs, len(classes)) != (2901, 12956, 9, 12947, 86):
        raise AssertionError((len(plain), len(cipher), len(sections), pairs, len(classes)))
    class_counts = Counter(classes)
    letter_counts = Counter(plain)
    marker_rows = []
    for letter in range(29):
        lam = pairs * letter_counts[letter] / len(plain)
        p = poisson_two_tail(86, lam)
        compatible_count = p >= 1e-6
        llr = marker_llr(classes, plain_words, letter) if compatible_count else None
        marker_rows.append({"rune": labels[letter], "index": letter, "expected_doublets": lam,
                            "count_p": p, "count_compatible": compatible_count,
                            "position_llr": llr,
                            "source_rule_excluded": p < 1e-6 or (llr is not None and llr <= -10)})
    q = [letter_counts[x] / len(plain) for x in range(29)]
    best, allocation = homophonic_min_chi2(q, len(cipher))
    observed_counts = Counter(cipher)
    observed_chi2 = math.fsum((observed_counts[x] - len(cipher) / 29) ** 2 / (len(cipher) / 29)
                              for x in range(29))
    return {
        "schema": "liberpedia-wulfic-q-results-v1", "input_sha256": hashes,
        "plain_runes": len(plain), "lp2_runes": len(cipher), "lp2_sections": len(sections),
        "lp2_pair_opportunities": pairs, "lp2_doublets": len(classes),
        "doublet_word_classes": {c: class_counts[c] for c in WORD_CLASSES},
        "C3": {"source_count_p_cutoff": 1e-6, "source_position_llr_cutoff": -10,
               "letters_checked": 29, "count_compatible": [r["rune"] for r in marker_rows if r["count_compatible"]],
               "excluded_under_source_rule": sum(r["source_rule_excluded"] for r in marker_rows),
               "rows": marker_rows},
        "C15": {"used_plain_runes": sum(bool(x) for x in letter_counts.values()),
                "spare_cipher_runes": 29 - sum(bool(x) for x in letter_counts.values()),
                "minimum_expected_chi2": best, "source_exclusion_cutoff": 200,
                "observed_lp2_chi2": observed_chi2,
                "optimal_allocation": [{"index": i, "rune": labels[i], "cipher_symbols": count}
                                       for i, count in enumerate(allocation) if count]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    path = HERE / "results.json"
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if path.read_text(encoding="utf-8") != encoded:
            raise AssertionError("result differs from clean site-data replay")
        print("PASS: independent LP2 and solved-reading site replay")
    else:
        path.write_text(encoded, encoding="utf-8", newline="\n")
        print("Wrote", path)


if __name__ == "__main__":
    main()
