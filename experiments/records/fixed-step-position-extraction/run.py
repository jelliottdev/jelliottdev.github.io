"""All fixed-step LP2 extractions, complete phase search and shared controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MODULUS = 26 ** 4


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@njit
def score_one(corpus, positions, start, stop, symbol_letters, symbol_sizes, frequencies):
    state = 0
    letters = 0
    total = 0.0
    quads = 0
    for j in range(start, stop):
        source = positions[j]
        if source < 0:
            state = 0
            letters = 0
            continue
        symbol = corpus[source]
        for k in range(symbol_sizes[symbol]):
            state = (state * 26 + symbol_letters[symbol, k]) % MODULUS
            letters += 1
            if letters >= 4:
                total += frequencies[state]
                quads += 1
    return total / quads, quads


@njit
def score_all(corpus, positions, starts, stops, symbol_letters, symbol_sizes, frequencies):
    scores = np.empty(len(starts), dtype=np.float64)
    quads = np.empty(len(starts), dtype=np.int64)
    for case in range(len(starts)):
        scores[case], quads[case] = score_one(corpus, positions, starts[case], stops[case],
                                             symbol_letters, symbol_sizes, frequencies)
    return scores, quads


def load():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    for entry in plan["inputs"]:
        assert sha((ROOT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {entry["rune"]: index for index, entry in enumerate(alphabet)}
    pages = []
    for page in plan["targets"]:
        raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        pages.append([lookup[rune] for rune in raw if rune in lookup])
    lengths = [len(page) for page in pages]
    corpus = np.array([symbol for page in pages for symbol in page], dtype=np.int64)
    letters = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, entry in enumerate(alphabet):
        sizes[i] = len(entry["latin"])
        for j, character in enumerate(entry["latin"]):
            letters[i, j] = ord(character) - 65
    counts = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        counts[gram] = int(count)
    normalization = math.log10(sum(counts.values()))
    frequencies = np.full(MODULUS, math.log10(0.01) - normalization, dtype=np.float64)
    for gram, count in counts.items():
        state = 0
        for letter in gram:
            state = 26 * state + ord(letter) - 65
        frequencies[state] = math.log10(count) - normalization
    readings = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in readings["controls"]}
    known = [symbol for section in plan["source_reading_ids"]
             for page in by_id[section]["decoded_pages"] for symbol in page["rune_indices"]]
    return plan, plan_bytes, alphabet, pages, lengths, corpus, letters, sizes, frequencies, known


def cases(lengths: list[int]):
    positions = []
    starts = []
    stops = []
    specs = []
    page_starts = [0]
    for length in lengths:
        page_starts.append(page_starts[-1] + length)
    for period in range(2, 30):
        for phase in range(period):
            for boundary in ("page-local", "joined"):
                starts.append(len(positions))
                if boundary == "page-local":
                    for start, length in zip(page_starts, lengths):
                        positions.extend(start + j for j in range(phase, length, period))
                        positions.append(-1)
                else:
                    positions.extend(range(phase, page_starts[-1], period))
                stops.append(len(positions))
                specs.append({"id": f"step{period:02}-phase{phase:02}-{boundary}",
                              "period": period, "phase": phase, "boundary": boundary})
    assert len(specs) == 868
    return (specs, np.array(positions, dtype=np.int32), np.array(starts, dtype=np.int32),
            np.array(stops, dtype=np.int32))


def portable_score(corpus, positions, start, stop, labels, table, floor):
    segments = []
    buffer = []
    for position in positions[start:stop]:
        if position < 0:
            segments.append("".join(buffer))
            buffer = []
        else:
            buffer.append(labels[int(corpus[position])])
    if buffer:
        segments.append("".join(buffer))
    values = [table.get(text[i:i + 4], floor)
              for text in segments for i in range(len(text) - 3)]
    return sum(values) / len(values), len(values)


def verified_grid(loaded):
    plan, plan_bytes, alphabet, pages, lengths, corpus, letters, sizes, frequencies, known = loaded
    specs, positions, starts, stops = cases(lengths)
    scores, quads = score_all(corpus, positions, starts, stops, letters, sizes, frequencies)
    assert min(quads) >= 100
    counts = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        counts[gram] = int(count)
    norm = math.log10(sum(counts.values()))
    table = {gram: math.log10(value) - norm for gram, value in counts.items()}
    floor = math.log10(0.01) - norm
    labels = [entry["latin"] for entry in alphabet]
    for index in (0, 1, 34, 35, 200, 459, 866, 867):
        value, n = portable_score(corpus, positions, starts[index], stops[index], labels, table, floor)
        assert n == quads[index] and math.isclose(value, scores[index], abs_tol=1e-10)
    return specs, positions, starts, stops, scores, quads


def plants(corpus, positions, starts, stops, known, letters, sizes, frequencies):
    rng = random.Random(33017122)
    base = np.array([rng.randrange(29) for _ in corpus], dtype=np.int64)
    controls = []
    for start, stop in zip(starts, stops):
        planted = base.copy()
        used = 0
        for index in positions[start:stop]:
            if index >= 0:
                planted[index] = known[used % len(known)]
                used += 1
        assert [int(planted[index]) for index in positions[start:stop] if index >= 0] == [known[i % len(known)] for i in range(used)]
        value, _ = score_one(planted, positions, start, stop, letters, sizes, frequencies)
        if value <= -5.5:
            raise ValueError(f"Planted score below fixed recognition threshold: {value}")
        controls.append(value)
    return controls


def streams_tsv(corpus, alphabet, specs, positions, starts, stops):
    runes = [entry["rune"] for entry in alphabet]
    labels = [entry["latin"] for entry in alphabet]
    lines = ["id\trune_segments\tlatin_segments\tselected_runes"]
    for case, spec in enumerate(specs):
        rune = []
        latin = []
        selected = 0
        for position in positions[starts[case]:stops[case]]:
            if position < 0:
                rune.append("|")
                latin.append("|")
            else:
                symbol = int(corpus[position])
                rune.append(runes[symbol])
                latin.append(labels[symbol])
                selected += 1
        lines.append(f"{spec['id']}\t{''.join(rune).rstrip('|')}\t{''.join(latin).rstrip('|')}\t{selected}")
    output = "\n".join(lines) + "\n"
    (HERE / "streams.tsv").write_text(output, encoding="utf-8", newline="\n")
    return sha(output.encode("utf-8"))


def report(benchmark=False, plant_only=False):
    loaded = load()
    plan, plan_bytes, alphabet, pages, lengths, corpus, letters, sizes, frequencies, known = loaded
    start_time = time.perf_counter()
    specs, positions, starts, stops, observed, observed_quads = verified_grid(loaded)
    print(f"Observed 868-case grid: {time.perf_counter()-start_time:.3f} s")
    controls = plants(corpus, positions, starts, stops, known, letters, sizes, frequencies)
    print(f"868 planted controls: {time.perf_counter()-start_time:.3f} s")
    if plant_only:
        return None
    trial_rng = random.Random(33017121)
    sample = corpus.copy()
    cursor = 0
    for length in lengths:
        slice_values = sample[cursor:cursor + length].tolist()
        trial_rng.shuffle(slice_values)
        sample[cursor:cursor + length] = slice_values
        cursor += length
    sample_scores, sample_quads = score_all(sample, positions, starts, stops, letters, sizes, frequencies)
    assert min(sample_quads) >= 100
    print(f"One 868-case shared-shuffle trial: {time.perf_counter()-start_time:.3f} s cumulative")
    if benchmark:
        return None
    maxima = []
    best_case = []
    maxima.append(float(np.max(sample_scores)))
    best_case.append(int(np.argmax(sample_scores)))
    for trial in range(1, 256):
        rng = random.Random(33017121 + trial)
        shuffled = corpus.copy()
        cursor = 0
        for length in lengths:
            values = shuffled[cursor:cursor + length].tolist()
            rng.shuffle(values)
            shuffled[cursor:cursor + length] = values
            cursor += length
        scores, quads = score_all(shuffled, positions, starts, stops, letters, sizes, frequencies)
        assert min(quads) >= 100
        maxima.append(float(np.max(scores)))
        best_case.append(int(np.argmax(scores)))
    best = int(np.argmax(observed))
    exceeded = int(sum(value >= observed[best] for value in maxima))
    stream_sha = streams_tsv(corpus, alphabet, specs, positions, starts, stops)
    result = {
        "schema": "liberpedia-fixed-step-extraction-v1",
        "plan_sha256": sha(plan_bytes),
        "total_runes": len(corpus),
        "case_count": len(specs),
        "observed": [{**spec, "selected_runes": int(sum(positions[starts[i]:stops[i]] >= 0)),
                      "latin_quadgrams": int(observed_quads[i]), "score": float(observed[i])}
                     for i, spec in enumerate(specs)],
        "planted_controls": {"count": len(controls), "minimum_score": float(min(controls)), "maximum_score": float(max(controls)), "all_above_threshold": True},
        "null_global_maxima": [{"seed": 33017121 + i, "score": maxima[i], "case": specs[best_case[i]]["id"]} for i in range(256)],
        "observed_best": {"case": specs[best]["id"], "score": float(observed[best])},
        "null_at_or_above_observed": exceeded,
        "empirical_global_p": (exceeded + 1) / 257,
        "streams_sha256": stream_sha,
    }
    print(f"Full null completed: {time.perf_counter()-start_time:.3f} s")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--plant-only", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report(benchmark=args.benchmark, plant_only=args.plant_only)
    if result is None:
        pass
    elif args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: 868-case observed grid, 868 planted controls and 256 shared full-grid shuffles")
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"best": result["observed_best"], "null_at_or_above": result["null_at_or_above_observed"]}))
