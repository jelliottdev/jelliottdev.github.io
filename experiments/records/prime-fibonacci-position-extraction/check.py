"""Independent page-JSON, trial-division and counted-quadgram replay."""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def positions(size: int, family: str) -> list[int]:
    if family == "prime":
        return [value - 1 for value in range(2, size + 1)
                if all(value % divisor for divisor in range(2, math.isqrt(value) + 1))]
    values = set()
    a, b = 1, 1
    while a <= size:
        values.add(a - 1)
        a, b = b, a + b
    return sorted(values)


def extract(pages: list[list[int]], arm: str) -> list[list[int]]:
    family = arm.split("-")[0]
    if arm.endswith("joined"):
        joined = sum(pages, [])
        return [[joined[i] for i in positions(len(joined), family)]]
    return [[page[i] for i in positions(len(page), family)] for page in pages]


def score(chunks: list[list[int]], labels: list[str], counts: dict[str, int], total: int) -> tuple[float | None, int]:
    seen = Counter()
    for chunk in chunks:
        text = "".join(labels[symbol] for symbol in chunk)
        seen.update(text[i:i + 4] for i in range(len(text) - 3))
    amount = sum(seen.values())
    if amount < 100:
        return None, amount
    numerator = sum(n * math.log10(counts.get(gram, 0.01) / total) for gram, n in seen.items())
    return numerator / amount, amount


def replay() -> None:
    plan_bytes = (HERE / "plan.json").read_bytes()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256(plan_bytes).hexdigest()
    plan = json.loads(plan_bytes)
    for source in plan["inputs"]:
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {entry["rune"]: i for i, entry in enumerate(alphabet)}
    labels = [entry["latin"] for entry in alphabet]
    pages = []
    for page_id in plan["targets"]:
        record = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))
        page = [lookup[character] for line in record["lines"] for character in line["raw"] if character in lookup]
        assert len(page) == record["rune_count"]
        pages.append(page)
    table = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        table[gram] = int(count)
    total = sum(table.values())
    for arm in plan["arms"]:
        chunks = extract(pages, arm)
        assert chunks == [row["indices"] for row in result["extracted"][arm]]
        actual, quads = score(chunks, labels, table, total)
        saved = result["observed"][arm]
        assert quads == saved["latin_quadgrams"]
        assert (actual is None and saved["score"] is None) or math.isclose(actual, saved["score"], abs_tol=1e-10)
    assert len(result["null_trials"]) == 256
    for trial, saved in enumerate(result["null_trials"]):
        rng = random.Random(33017119 + trial)
        transformed = [page.copy() for page in pages]
        for page in transformed:
            rng.shuffle(page)
        assert saved["seed"] == 33017119 + trial
        scores = {}
        for arm in result["eligible_arms"]:
            value, _ = score(extract(transformed, arm), labels, table, total)
            assert math.isclose(value, saved["arm_scores"][arm], abs_tol=1e-10)
            scores[arm] = value
        assert math.isclose(max(scores.values()), saved["global_max"], abs_tol=1e-10)
    print("PASS: independent page-JSON extraction and 256 shared global controls")


if __name__ == "__main__":
    replay()
