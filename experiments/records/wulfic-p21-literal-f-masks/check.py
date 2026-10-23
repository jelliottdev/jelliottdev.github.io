"""Independent scalar exhaustive check of every published manuscript F mask."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ALPHABET = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
BREAKS = {".", "-", "•", " ", "\n"}


def raw_values_and_singletons(raw: str) -> tuple[list[int], set[int]]:
    vals = []
    lengths = []
    current = 0
    for ch in raw:
        if ch in ALPHABET:
            vals.append(ALPHABET.index(ch)); current += 1
        elif ch in BREAKS and current:
            lengths.append(current); current = 0
    if current:
        lengths.append(current)
    pos = 0
    singles = set()
    for length in lengths:
        if length == 1:
            singles.add(pos)
        pos += length
    assert pos == len(vals)
    return vals, singles


def check_page(row: dict, pin: dict, cipher: list[int] | None = None) -> None:
    from_input, singletons = raw_values_and_singletons(pin["raw"])
    if cipher is None:
        cipher = from_input
    assert len(cipher) == row["runes"] and len(singletons) == row["singleton_count"]
    key = row["parsed_key"]
    zeros = [i for i, c in enumerate(cipher) if c == 0]
    assert len(zeros) == row["cipher_F_count"]
    gated_count = 0
    max_ioc = -1.0
    max_mask = -1
    base_ioc = -1.0
    for bits in range(1 << len(zeros)):
        mask = {zeros[j] for j in range(len(zeros)) if bits & (1 << j)}
        out = []
        ki = 0
        for i, c in enumerate(cipher):
            if i in mask:
                out.append(0)
                continue
            k = key[ki % len(key)]
            if row["mode"] == "sub":
                out.append((c - k) % 29)
            elif row["mode"] == "add":
                out.append((c + k) % 29)
            else:
                out.append((k - c) % 29)
            ki += 1
        f = collections.Counter(out)
        ioc = 29 * sum(v * (v - 1) for v in f.values()) / (len(out) * (len(out) - 1))
        if bits == 0:
            base_ioc = ioc
        if ioc > max_ioc:
            max_ioc, max_mask = ioc, bits
        if singletons and all(out[i] in (10, 24) for i in singletons):
            gated_count += 1
    assert row["mask_count"] == (1 << len(zeros))
    assert row["all_singleton_masks"] == gated_count
    assert abs(row["baseline_ioc"] - base_ioc) < 1e-12
    assert abs(row["best_ioc"] - max_ioc) < 1e-12
    assert row["best_ioc_mask"] == [zeros[j] for j in range(len(zeros)) if max_mask & (1 << j)]


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    source = json.loads((HERE / "source-run.json").read_text(encoding="utf8"))
    pin = json.loads((HERE / "inputs.json").read_text(encoding="utf8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    assert result["inputs_sha256"] == hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest()
    assert result["gate_sha256"] == hashlib.sha256((HERE / "gate.json").read_bytes()).hexdigest()
    assert len(result["observed"]["pages"]) == len(source["pages"]) == len(pin["pages"]) == 10
    for row, src, page in zip(result["observed"]["pages"], source["pages"], pin["pages"]):
        assert row["source_page"] == src["source_page"] == page["source_page"]
        check_page(row, page)
        assert src["status"] == "best-ioc-fallback"
        assert row["second_layer"]["route_count"] == 45
        assert row["second_layer"]["printed_count"] == 0
        assert all(route["length"] > 0 and len(route["sha256"]) == 64 for route in row["second_layer"]["routes"])
    assert sum(r["mask_count"] for r in result["observed"]["pages"]) == result["observed"]["total_masks"] == 27402
    assert result["observed"]["gated_page_count"] == 0
    controls = result["controls"]["rows"]
    assert len(controls) == 19
    rng = np.random.default_rng(20261023)
    for rep, saved in enumerate(controls):
        assert saved["replicate"] == rep
        for page, row in zip(pin["pages"], saved["per_page"]):
            assert row["current_page"] == page["current_page"]
            raw, _ = raw_values_and_singletons(page["raw"])
            shuffled = list(rng.permutation(np.asarray(raw, dtype=np.int16)))
            assert collections.Counter(shuffled) == collections.Counter(raw)
            if rep == 0:
                template = next(r for r in result["observed"]["pages"] if r["current_page"] == row["current_page"])
                # Recompute the entire first shuffled grid without relying on the runner.
                # Its page-level count is the criterion; best-IoC fields differ by shuffle.
                # Direct count under all subsets, using the same scalar recurrence.
                zeros = [i for i, c in enumerate(shuffled) if c == 0]
                _, singles = raw_values_and_singletons(page["raw"])
                passing = 0
                for bits in range(1 << len(zeros)):
                    mask = {zeros[j] for j in range(len(zeros)) if bits & (1 << j)}
                    out = []
                    ki = 0
                    for i, c in enumerate(shuffled):
                        if i in mask:
                            out.append(0)
                        else:
                            k = template["parsed_key"][ki % len(template["parsed_key"])]
                            out.append(((c-k) if template["mode"] == "sub" else
                                        (c+k) if template["mode"] == "add" else (k-c)) % 29)
                            ki += 1
                    passing += bool(singles and all(out[i] in (10, 24) for i in singles))
                assert passing == row["all_singleton_masks"]
        assert saved["gated_page_count"] == sum(r["all_singleton_masks"] > 0 for r in saved["per_page"])
        assert saved["best_gated_score"] is None
    print("All 27,402 manuscript masks and the first complete shuffled search independently checked.")


if __name__ == "__main__":
    main()
