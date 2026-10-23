"""Post-observation ordered-English key diagnostic; see frozen GP control plan."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

from fast_check import load, search_pages

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def gp_key(text: str, alphabet: list[dict]) -> list[int]:
    normalized = "".join(letter for letter in text.upper() if "A" <= letter <= "Z")
    labels = sorted(((row["latin"], index) for index, row in enumerate(alphabet)),
                    key=lambda pair: -len(pair[0]))
    aliases = {"V": 1, "K": 5, "Z": 15, "Q": 5}
    key = []
    cursor = 0
    while cursor < len(normalized):
        for label, index in labels:
            if normalized.startswith(label, cursor):
                key.append(index)
                cursor += len(label)
                break
        else:
            key.append(aliases[normalized[cursor]])
            cursor += 1
    return key


def run() -> None:
    control_plan_bytes = (HERE / "english-key-gp-control-plan.json").read_bytes()
    diagnostic = json.loads(control_plan_bytes)
    source_path = ROOT / diagnostic["source"]
    source_bytes = source_path.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == diagnostic["source_sha256"]
    paragraphs = json.loads(source_bytes.decode("utf-8"))
    assert len(paragraphs) == 50
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    key = gp_key(" ".join(paragraph["text"] for paragraph in paragraphs), alphabet)
    assert max(diagnostic["windows"]) + diagnostic["window_length"] <= len(key)
    plan, primary, pages, lengths, _, symbols, sizes, frequencies = load()
    rows = []
    start = time.perf_counter()
    for first in diagnostic["windows"]:
        window = key[first:first + diagnostic["window_length"]]
        winners = search_pages(pages, lengths, np.array(window, dtype=np.int64),
                               symbols, sizes, frequencies)
        best = int(np.argmax(winners[:, 0]))
        rows.append({
            "source_start": first,
            "key_sha256": hashlib.sha256(bytes(window)).hexdigest(),
            "global_best": {
                "page": plan["targets"][best],
                "score": float(winners[best, 0]),
                "offset": int(winners[best, 1]),
                "sign": int(winners[best, 2]),
            },
        })
    elapsed = time.perf_counter() - start
    output = {
        "schema": "liberpedia-solved-reading-running-key-english-gp-control-v1",
        "control_plan_sha256": hashlib.sha256(control_plan_bytes).hexdigest(),
        "primary_plan_sha256": primary["plan_sha256"],
        "emerson_key_runes": len(key),
        "emerson_key_sha256": hashlib.sha256(bytes(key)).hexdigest(),
        "windows": rows,
    }
    (HERE / "english-key-gp-control-results.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"seconds": elapsed, "windows": rows}, indent=2))


if __name__ == "__main__":
    run()
