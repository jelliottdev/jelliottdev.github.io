"""A bounded four-phase concentration check on LP2 rune-bearing pages."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], portion: float) -> float:
    ordered = sorted(values)
    return ordered[round(portion * (len(ordered) - 1))]


def load() -> tuple[dict, list[list[int]], list[int]]:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    if plan["schema"] != "liberpedia-four-phase-ioc-plan-v1":
        raise ValueError("Unexpected plan")
    inputs = plan["input_manifest"]
    if digest(ROOT / inputs["alphabet_path"]) != inputs["alphabet_sha256"]:
        raise ValueError("Alphabet index changed")
    if digest(ROOT / inputs["positive_control_path"]) != inputs["positive_control_sha256"]:
        raise ValueError("Positive-control ciphertext changed")
    index = json.loads((ROOT / inputs["alphabet_path"]).read_text(encoding="utf-8"))
    alphabet = {item["rune"]: i for i, item in enumerate(index["alphabet"])}
    if len(alphabet) != 29:
        raise ValueError("Expected 29 GP runes")

    names = [f"lp2-{i:02d}" for i in range(56) if i != 50]
    h = hashlib.sha256()
    pages: list[list[int]] = []
    for name in names:
        raw = (ROOT / "text" / f"{name}.txt").read_bytes()
        h.update(name.encode("ascii") + b"\0" + raw + b"\0")
        page = raw.decode("utf-8")
        unknown = {c for c in page if "\u16a0" <= c <= "\u16ff"} - alphabet.keys()
        if unknown:
            raise ValueError(f"Unmapped runes on {name}: {unknown}")
        pages.append([alphabet[c] for c in page if c in alphabet])
    if h.hexdigest() != inputs["text_name_byte_sha256"]:
        raise ValueError("LP2 source pages changed")
    if len(pages) != 55 or sum(map(len, pages)) != 12956:
        raise ValueError("Source page mapping differs from frozen stream")
    warning = [alphabet[c] for c in (ROOT / inputs["positive_control_path"]).read_text(encoding="utf-8") if c in alphabet]
    if len(warning) != 184:
        raise ValueError("Expected 184 warning-page runes")
    return plan, pages, warning


def ioc(seq: list[int]) -> float:
    counts = Counter(seq)
    n = len(seq)
    return sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


def phase_iocs(stream: list[int]) -> list[float]:
    return [ioc(stream[phase::4]) for phase in range(4)]


def stats(stream: list[int]) -> tuple[list[float], float, float]:
    phases = phase_iocs(stream)
    return phases, sum(phases) / 4, max(phases)


def shuffled_pages(pages: list[list[int]], rng: random.Random) -> list[int]:
    result = []
    for page in pages:
        shuffled = page.copy()
        rng.shuffle(shuffled)
        result.extend(shuffled)
    return result


def report() -> dict:
    plan, pages, warning = load()
    actual_stream = [x for page in pages for x in page]
    observed, mean, maximum = stats(actual_stream)
    rng = random.Random(plan["seed"])
    null_phases: list[list[float]] = []
    null_mean: list[float] = []
    null_max: list[float] = []
    for _ in range(plan["null_trials"]):
        phases, m, high = stats(shuffled_pages(pages, rng))
        null_phases.append(phases)
        null_mean.append(m)
        null_max.append(high)

    # Each copy is a known Atbash reading under its own fixed additive shift.
    decoded = [(28 - value) % 29 for value in warning]
    shifts = [0, 3, 7, 11]
    planted = [((decoded[i] + shifts[phase]) % 29)
               for i in range(len(decoded)) for phase in range(4)]
    planted_phases, planted_mean, planted_max = stats(planted)
    control_rng = random.Random(plan["seed"] + 1)
    control_null_mean = []
    for _ in range(plan["null_trials"]):
        shuffled = planted.copy()
        control_rng.shuffle(shuffled)
        control_null_mean.append(stats(shuffled)[1])

    mean_count = sum(v >= mean for v in null_mean)
    max_count = sum(v >= maximum for v in null_max)
    control_count = sum(v >= planted_mean for v in control_null_mean)
    denom = plan["null_trials"] + 1
    return {
        "schema": "liberpedia-four-phase-ioc-results-v1",
        "source_revision": plan["source"]["revision"],
        "page_mapping": "LP2-00–55 excluding number-only LP2-50; 55 rune-bearing pages",
        "page_count": len(pages),
        "rune_count": len(actual_stream),
        "phase_sizes": [len(actual_stream[phase::4]) for phase in range(4)],
        "observed": {"phase_ioc": observed, "mean_phase_ioc": mean, "max_phase_ioc": maximum},
        "null": {
            "trials": plan["null_trials"],
            "seed": plan["seed"],
            "phase_medians": [percentile([row[p] for row in null_phases], 0.5) for p in range(4)],
            "phase_central_95": [[percentile([row[p] for row in null_phases], q) for q in (0.025, 0.975)] for p in range(4)],
            "mean_median": percentile(null_mean, 0.5),
            "mean_central_95": [percentile(null_mean, q) for q in (0.025, 0.975)],
            "max_median": percentile(null_max, 0.5),
            "max_central_95": [percentile(null_max, q) for q in (0.025, 0.975)],
            "mean_at_least_observed": mean_count,
            "max_at_least_observed": max_count,
            "mean_upper_p": (mean_count + 1) / denom,
            "max_upper_p": (max_count + 1) / denom,
            "two_measure_adjusted_min_p": min(1, 2 * min((mean_count + 1) / denom, (max_count + 1) / denom)),
        },
        "planted_control": {
            "description": "Four separately shifted copies of the 184-rune Atbash-decoded LP1 warning page, position-interleaved",
            "shifts": shifts,
            "phase_ioc": planted_phases,
            "mean_phase_ioc": planted_mean,
            "max_phase_ioc": planted_max,
            "whole_stream_shuffle_at_least_planted": control_count,
            "whole_stream_shuffle_upper_p": (control_count + 1) / denom,
            "null_mean_central_95": [percentile(control_null_mean, q) for q in (0.025, 0.975)]
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    target = HERE / "results.json"
    if args.check:
        if json.loads(target.read_text(encoding="utf-8")) != result:
            raise SystemExit("FAIL: saved results differ from rerun")
        print("PASS: page mapping, phase scores, 1,999 page-shuffled controls and planted four-stream control")
    else:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"observed": result["observed"], "null": result["null"], "control": result["planted_control"]}, indent=2))


if __name__ == "__main__":
    main()
