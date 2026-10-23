#!/usr/bin/env python3
"""Independent rune recount and finite-probability check for the D2 audit."""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"


def main() -> None:
    manifest = json.loads((HERE / "source-manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        assert hashlib.sha256((SOURCE / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert "CONTROL_OK = True" in (HERE / "source-replay.txt").read_text(encoding="utf-8")
    raw = (SOURCE / "liber-primus/data/krisyotam_runes.txt").read_text(encoding="utf-8")
    pages = [[c for c in segment if "\u16a0" <= c <= "\u16ff"]
             for segment in raw.split("%")]
    pages = [p for p in pages if p]
    assert len(pages) == 57
    unsolved = pages[:-2]
    flat = [rune for page in unsolved for rune in page]
    edges = sum(len(page) - 1 for page in unsolved)
    doublets = sum(a == b for page in unsolved for a, b in zip(page, page[1:]))
    joins = sum(a[-1] == b[0] for a, b in zip(unsolved, unsolved[1:]))
    assert (len(flat), edges, doublets, joins) == (12956, 12901, 86, 0)
    counts = Counter(flat)
    assert len(counts) == 29
    ioc = 29 * sum(n * (n - 1) for n in counts.values()) / (len(flat) * (len(flat) - 1))
    entropy = -sum((n / len(flat)) * math.log2(n / len(flat)) for n in counts.values())
    assert round(ioc, 4) == report["measured_ioc_times_29"] == 0.9999
    assert round(entropy, 4) == report["measured_entropy_bits"] == 4.8565
    assert (report["measured_runes"], report["measured_within_page_edges"],
            report["measured_within_page_doublets"]) == (12956, 12901, 86)
    assert report["measured_cross_page_join_doublets"] == 0
    assert report["d2_control"]["passed"] and report["d2_control"]["planted_english_score"] > -5.5

    # Enumerate the *ciphertexts* directly. IID uniform keys yield each of the
    # 3^4 ciphertexts exactly once for a fixed plaintext under additive encryption.
    n = 3
    histogram = Counter(sum(a == b for a, b in zip(cipher, cipher[1:]))
                        for cipher in itertools.product(range(n), repeat=4))
    assert [histogram[i] for i in range(4)] == [24, 36, 18, 3]
    control = report["finite_independent_key_control"]
    assert control["ciphertext_doublet_count_distribution"] == [24, 36, 18, 3]
    assert Fraction(control["probability_of_below_floor_realization"]) == Fraction(8, 27)
    assert Fraction(control["expected_ciphertext_doublet_rate"]) == Fraction(1, 3)
    assert report["d2_script_recomputes_g3_floor"] is False
    assert report["b4_large_corpus_inputs_absent"] == ["kjv", "moby", "pride", "war"]
    assert report["b4_preregistered_minimum_large_corpora"] == 5
    assert report["b4_implemented_large_corpora"] == 4
    assert report["b4_original_reported_large_corpus_min_pct"] == 1.5025075125375627
    later = report["l7_later_reported_floor"]["published_corpora_recomputed"]
    assert abs(later["kjv"]["min_pct"] - 1.3861557113716574) < 1e-12
    print("D2 rune counts, source hashes, and finite model check passed independently")


if __name__ == "__main__":
    main()
