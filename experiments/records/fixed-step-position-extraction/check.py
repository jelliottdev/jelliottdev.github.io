"""Independent page-JSON replay with a four-character ring quadgram scorer."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


@njit
def score_grid(stream, locs, begin, end, chars, sizes, model):
    scores = np.empty(len(begin), dtype=np.float64)
    quads = np.empty(len(begin), dtype=np.int64)
    for candidate in range(len(begin)):
        a = b = c = d = 0
        seen = 0
        total = 0.0
        count = 0
        for p in range(begin[candidate], end[candidate]):
            locus = locs[p]
            if locus < 0:
                seen = 0
                continue
            symbol = stream[locus]
            for k in range(sizes[symbol]):
                new = chars[symbol, k]
                if seen == 0:
                    a = new
                elif seen == 1:
                    b = new
                elif seen == 2:
                    c = new
                elif seen == 3:
                    d = new
                    total += model[((a * 26 + b) * 26 + c) * 26 + d]
                    count += 1
                else:
                    a, b, c, d = b, c, d, new
                    total += model[((a * 26 + b) * 26 + c) * 26 + d]
                    count += 1
                seen += 1
        scores[candidate] = total / count
        quads[candidate] = count
    return scores, quads


def index_cases(lengths):
    start_pages = [0]
    for length in lengths:
        start_pages.append(start_pages[-1] + length)
    ids, sites, begins, ends = [], [], [], []
    for step in range(2, 30):
        for phase in range(step):
            for boundary in ("page-local", "joined"):
                ids.append(f"step{step:02}-phase{phase:02}-{boundary}")
                begins.append(len(sites))
                if boundary == "page-local":
                    for page_index, length in enumerate(lengths):
                        sites += [start_pages[page_index] + position
                                  for position in range(length) if position % step == phase]
                        sites.append(-1)
                else:
                    sites += [position for position in range(start_pages[-1]) if position % step == phase]
                ends.append(len(sites))
    return ids, np.array(sites, dtype=np.int32), np.array(begins, dtype=np.int32), np.array(ends, dtype=np.int32)


def replay():
    raw = (HERE / "plan.json").read_bytes()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256(raw).hexdigest()
    plan = json.loads(raw)
    for entry in plan["inputs"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    runes = [entry["rune"] for entry in alphabet]
    labels = [entry["latin"] for entry in alphabet]
    lookup = {rune: i for i, rune in enumerate(runes)}
    page_streams = []
    for page_id in plan["targets"]:
        page = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))
        values = [lookup[rune] for line in page["lines"] for rune in line["raw"] if rune in lookup]
        assert len(values) == page["rune_count"]
        page_streams.append(values)
    lengths = [len(page) for page in page_streams]
    corpus = np.array([rune for page in page_streams for rune in page], dtype=np.int64)
    ids, locs, begins, ends = index_cases(lengths)
    assert ids == [row["id"] for row in result["observed"]]
    data = (HERE / "streams.tsv").read_bytes()
    assert hashlib.sha256(data).hexdigest() == result["streams_sha256"]
    saved_lines = data.decode("utf-8").splitlines()
    assert saved_lines[0] == "id\trune_segments\tlatin_segments\tselected_runes"
    assert len(saved_lines) == 869
    for i, identifier in enumerate(ids):
        expected_runes = []
        expected_latin = []
        n = 0
        for locus in locs[begins[i]:ends[i]]:
            if locus < 0:
                expected_runes.append("|")
                expected_latin.append("|")
            else:
                symbol = corpus[locus]
                expected_runes.append(runes[symbol])
                expected_latin.append(labels[symbol])
                n += 1
        assert saved_lines[i + 1] == f"{identifier}\t{''.join(expected_runes).rstrip('|')}\t{''.join(expected_latin).rstrip('|')}\t{n}"
    counts = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = line.split()
        counts[gram] = int(amount)
    normalization = math.log10(sum(counts.values()))
    model = np.full(26 ** 4, math.log10(0.01) - normalization, dtype=np.float64)
    for gram, amount in counts.items():
        code = 0
        for character in gram:
            code = 26 * code + ord(character) - 65
        model[code] = math.log10(amount) - normalization
    chars = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for symbol, label in enumerate(labels):
        sizes[symbol] = len(label)
        for j, char in enumerate(label):
            chars[symbol, j] = ord(char) - 65
    scores, quads = score_grid(corpus, locs, begins, ends, chars, sizes, model)
    for i, saved in enumerate(result["observed"]):
        assert int(quads[i]) == saved["latin_quadgrams"]
        assert math.isclose(float(scores[i]), saved["score"], rel_tol=0, abs_tol=1e-10)
    assert len(result["null_global_maxima"]) == 256
    for trial, saved in enumerate(result["null_global_maxima"]):
        rng = random.Random(33017121 + trial)
        pages = [page.copy() for page in page_streams]
        for page in pages:
            rng.shuffle(page)
        shuffled = np.array([rune for page in pages for rune in page], dtype=np.int64)
        scores, quads = score_grid(shuffled, locs, begins, ends, chars, sizes, model)
        assert min(quads) >= 100
        best = int(np.argmax(scores))
        assert saved["seed"] == 33017121 + trial and saved["case"] == ids[best]
        assert math.isclose(float(scores[best]), saved["score"], rel_tol=0, abs_tol=1e-10)
    print("PASS: independent page JSON and ring-scorer replay of 868 cases and all 256 full-grid controls")


if __name__ == "__main__":
    replay()
