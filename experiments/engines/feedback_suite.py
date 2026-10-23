"""Run any gp29-feedback-v1 manifest against fixed known-opening cribs.

Use --manifest to select a different bounded suite; --output-dir directs the
deterministic cases.json and results.json artifacts. No AI, network or scorer.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
from engines.feedback import decode, encrypt, page_symbols  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serialized(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_manifest(path: Path):
    raw = path.read_bytes()
    spec = json.loads(raw)
    assert spec["schema"] == "liberpedia-feedback-suite-manifest-v1"
    assert spec["engine"] == "gp29-feedback-v1"
    assert all(1 <= lag <= 16 for lag in spec["lags"])
    assert all(0 <= primer <= 28 for primer in spec["primers"])
    assert set(spec["modes"]) <= {"ciphertext", "plaintext"}
    assert set(spec["boundaries"]) <= {"continuous", "word-reset"}
    assert len(spec["pages"]) == len(set(spec["pages"]))
    assert len(spec["cribs"]) == len({entry["id"] for entry in spec["cribs"]})
    assert all(entry["indices"] and all(0 <= value < 29 for value in entry["indices"])
               for entry in spec["cribs"])
    count = len(spec["modes"]) * len(spec["lags"]) * len(spec["primers"]) * len(spec["boundaries"])
    assert count == spec["declared_config_count"]
    return spec, sha(raw)


def read_inputs(spec):
    fingerprints = []
    alphabet_path = ROOT / spec["alphabet_path"]
    alphabet_raw = alphabet_path.read_bytes()
    alphabet = [entry["rune"] for entry in json.loads(alphabet_raw)["alphabet"]]
    assert len(alphabet) == len(set(alphabet)) == 29
    fingerprints.append({"path": spec["alphabet_path"], "sha256": sha(alphabet_raw)})
    if "crib_source_plan" in spec:
        ref = spec["crib_source_plan"]
        ref_raw = (ROOT / ref["path"]).read_bytes()
        assert sha(ref_raw) == ref["sha256"]
        prior = json.loads(ref_raw)["openings"]
        assert [(row["id"], row["indices"], row["source"], row["sha256"]) for row in spec["cribs"]] == [
            (row["id"], row["indices"], row["source"], row["sha256"]) for row in prior]
        fingerprints.append(ref)
    for crib in spec["cribs"]:
        raw = (ROOT / crib["source"]).read_bytes()
        assert sha(raw) == crib["sha256"], crib["source"]
        fingerprints.append({"path": crib["source"], "sha256": sha(raw)})
    pages = []
    for page in spec["pages"]:
        relative = spec["page_path_template"].format(page=page)
        raw = (ROOT / relative).read_bytes()
        symbols, starts = page_symbols(raw.decode("utf-8"), alphabet)
        assert symbols and len(symbols) >= max(len(crib["indices"]) for crib in spec["cribs"]), page
        pages.append((page, symbols, starts))
        fingerprints.append({"path": relative, "sha256": sha(raw)})
    return pages, fingerprints


def check_control(mode, lag, primer, boundary):
    # Multiple segment lengths exercise both an active lag and a short word
    # whose every rune uses the primer when lag exceeds that word's length.
    source = [(7 * i + i // 4 + 3) % 29 for i in range(45)]
    starts = [0] * 21 + [21] * 5 + [26] * 19 if boundary == "word-reset" else [0] * 45
    encrypted = encrypt(source, mode, lag, primer, starts)
    assert decode(encrypted, mode, lag, primer, starts) == source
    assert encrypted[: min(lag, 21)] == [(source[i] + primer) % 29 for i in range(min(lag, 21))]
    if boundary == "word-reset":
        assert encrypted[21] == (source[21] + primer) % 29
        assert encrypted[26] == (source[26] + primer) % 29


def case_id(mode, lag, primer, boundary):
    return f"{mode}-lag{lag:02}-primer{primer:02}-{boundary}"


def run_case(config, pages, cribs):
    mode, lag, primer, boundary = config
    check_control(mode, lag, primer, boundary)
    digest = hashlib.sha256()
    hits = []
    maximum = -1
    ties = []
    comparisons = 0
    for page, cipher, word_starts in pages:
        starts = [0] * len(cipher) if boundary == "continuous" else word_starts
        plain = decode(cipher, mode, lag, primer, starts)
        digest.update((page + "\t" + ",".join(map(str, plain)) + "\n").encode("utf-8"))
        for crib in cribs:
            indices = crib["indices"]
            prefix = 0
            while prefix < len(indices) and plain[prefix] == indices[prefix]:
                prefix += 1
            anchor = {"page": page, "opening": crib["id"]}
            if prefix == len(indices):
                hits.append(anchor)
            if prefix > maximum:
                maximum = prefix
                ties = [anchor]
            elif prefix == maximum:
                ties.append(anchor)
            comparisons += 1
    return {"id": case_id(*config), "mode": mode, "lag": lag, "primer": primer,
            "boundary": boundary, "decode_sha256": digest.hexdigest(),
            "comparison_count": comparisons, "opening_matches": hits,
            "max_prefix_length": maximum, "max_prefix_ties": ties}


def build(manifest_path: Path):
    """Return (deterministic summary, full case payload) for a suite manifest."""
    spec, manifest_sha = load_manifest(manifest_path)
    pages, fingerprints = read_inputs(spec)
    configs = itertools.product(spec["modes"], spec["lags"], spec["primers"], spec["boundaries"])
    cases = [run_case(config, pages, spec["cribs"]) for config in configs]
    assert len(cases) == spec["declared_config_count"]
    assert len({entry["id"] for entry in cases}) == len(cases)
    cases_payload = {"schema": "liberpedia-feedback-opening-cases-v1", "suite_id": spec["suite_id"], "cases": cases}
    cases_bytes = serialized(cases_payload)
    histogram = Counter(str(row["max_prefix_length"]) for row in cases)
    full_count = sum(len(row["opening_matches"]) for row in cases)
    best = max(row["max_prefix_length"] for row in cases)
    summary = {
        "schema": "liberpedia-feedback-opening-census-v1",
        "suite_id": spec["suite_id"],
        "engine": spec["engine"],
        "manifest_sha256": manifest_sha,
        "input_sha256": fingerprints,
        "cases_sha256": sha(cases_bytes),
        "case_count": len(cases),
        "page_count": len(pages),
        "crib_count": len(spec["cribs"]),
        "comparison_count": sum(row["comparison_count"] for row in cases),
        "synthetic_controls_passed": len(cases),
        "full_match_count": full_count,
        "full_match_cases": [row["id"] for row in cases if row["opening_matches"]],
        "best_prefix_length": best,
        "best_prefix_cases": [row["id"] for row in cases if row["max_prefix_length"] == best],
        "max_prefix_distribution": dict(sorted(histogram.items(), key=lambda pair: int(pair[0]))),
        "interpretation_limit": "Finite exact-opening screen only. No English score, later position, alternate primer, boundary model or decryption is inferred."
    }
    return summary, cases_payload


def main(default_manifest: Path | None = None, argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=default_manifest)
    parser.add_argument("--output-dir", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.manifest is None:
        parser.error("--manifest is required")
    if args.output_dir is None:
        args.output_dir = args.manifest.parent
    result, cases = build(args.manifest)
    cases_data, results_data = serialized(cases), serialized(result)
    if args.write:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "cases.json").write_bytes(cases_data)
        (args.output_dir / "results.json").write_bytes(results_data)
    else:
        assert cases_data == (args.output_dir / "cases.json").read_bytes(), "Case output changed"
        assert results_data == (args.output_dir / "results.json").read_bytes(), "Summary output changed"
    print(json.dumps({key: result[key] for key in ("case_count", "comparison_count", "full_match_count", "best_prefix_length")}))


if __name__ == "__main__":
    main()
