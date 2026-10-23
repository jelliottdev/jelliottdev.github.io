"""Independent page-JSON scanner and counted-quadgram full-grid replay."""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def recount(lines: list[str], runes: set[str]):
    line_counts = []
    word_counts = []
    word = 0
    for line in lines:
        line_count = 0
        for char in line:
            if char in runes:
                line_count += 1
                word += 1
            elif char == "-":
                if word:
                    word_counts.append(word)
                    word = 0
        if line_count:
            line_counts.append(line_count)
    if word:
        word_counts.append(word)
    return {"line-runes": line_counts, "word-runes": word_counts}


def evaluate(pages, labels, counts):
    total = sum(counts.values())
    rows = {}
    for source in ("line-runes", "word-runes"):
        for mapping in ("count", "count-minus-one"):
            decoded = [[(number - (mapping == "count-minus-one")) % 29 for number in page[source]] for page in pages]
            for boundary in ("page-local", "joined"):
                segments = decoded if boundary == "page-local" else [[symbol for page in decoded for symbol in page]]
                histogram = Counter()
                for segment in segments:
                    latin = "".join(labels[symbol] for symbol in segment)
                    histogram.update(latin[pos:pos + 4] for pos in range(len(latin) - 3))
                quads = sum(histogram.values())
                score = sum(n * math.log10(counts.get(gram, 0.01) / total)
                            for gram, n in histogram.items()) / quads if quads >= 100 else None
                rows[f"{source}-{mapping}-{boundary}"] = (score, quads, segments)
    return rows


def replay():
    raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(raw)
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(raw).hexdigest() == result["plan_sha256"]
    for entry in plan["inputs"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    runes = {entry["rune"] for entry in alphabet}
    labels = [entry["latin"] for entry in alphabet]
    pages = []
    for identifier in plan["targets"]:
        page = json.loads((ROOT / "data/pages" / f"{identifier}.json").read_text(encoding="utf-8"))
        counts = recount([line["raw"] for line in page["lines"]], runes)
        pages.append(counts)
    assert pages == result["page_counts"]
    table = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, number = line.split()
        table[gram] = int(number)
    observed = evaluate(pages, labels, table)
    assert list(observed) == plan["arms"]
    for name, (score, quads, segments) in observed.items():
        saved = result["observed"][name]
        assert quads == saved["latin_quadgrams"] and segments == saved["segments"]
        assert (score is None and saved["score"] is None) or math.isclose(score, saved["score"], abs_tol=1e-10)
    assert len(result["null_trials"]) == 256
    for trial, saved in enumerate(result["null_trials"]):
        rng = random.Random(33017125 + trial)
        transformed = [{source: values.copy() for source, values in page.items()} for page in pages]
        for page in transformed:
            rng.shuffle(page["line-runes"])
            rng.shuffle(page["word-runes"])
        values = evaluate(transformed, labels, table)
        assert saved["seed"] == 33017125 + trial
        for name in plan["arms"]:
            score = values[name][0]
            assert math.isclose(score, saved["arm_scores"][name], abs_tol=1e-10)
        best = max(plan["arms"], key=lambda name: values[name][0])
        assert best == saved["global_best"]["arm"]
        assert math.isclose(values[best][0], saved["global_best"]["score"], abs_tol=1e-10)
    print("PASS: independent page-JSON count scanner and all 256 shared eight-arm controls")


if __name__ == "__main__":
    replay()
