"""Refresh declared record hashes after edits; does not rerun scores."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/solved-reading-running-key/"


def item(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def make() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    input_paths = [
        PREFIX + name for name in (
            "plan.json", "check.py", "fast_check.py", "english-key-control-plan.json",
            "english-key-gp-control-plan.json", "english_key_control.py")
    ] + [entry["path"] for entry in plan["inputs"]]
    input_paths += ["exports/sources/emerson-paragraphs.json"]
    input_paths = list(dict.fromkeys(input_paths))
    output_paths = [PREFIX + name for name in (
        "results.json", "english-key-gp-control-results.json", "key-comparison.svg")]
    record = {
        "id": "solved-reading-running-key",
        "status": "draft",
        "title": "Solved manuscript readings as a running key",
        "question": "Does any complete unsolved LP2 page decode under a contiguous offset of the established GP29 readings?",
        "reader_question": "Could the solved pages be a key for the unsolved pages?",
        "summary": "A complete-page search over eight established readings produced no readable passage. The best short-page score exceeds 16 shuffled-key maxima and four post-observation English-source checks, but does not identify a decryption.",
        "finding": "Across 292,318 whole-page offset/sign alignments, the best English quadgram score was −5.897 on the 66-rune LP2-49. No one of 16 shuffled-key global maxima reached it (add-one estimate 1/17), but the output is not coherent English. Four later GP-encoded Emerson windows also scored below it.",
        "limitations": "The scorer favors short selected text, and 16 key shuffles plus four post-observation English windows are weak controls for the broad choice of structured keys. No independent continuation or readable plaintext was found. Only this source order, direct additive GP29 rule, and complete pages were searched.",
        "next_steps": "A proposed key interpretation needs a predeclared new source/clock rule and must predict a readable complete passage plus unseen continuation; compare the whole selection process with natural-key controls.",
        "outcome": "inconclusive",
        "tags": ["running key", "known readings", "Gematria Primus", "English scorer", "full-page search", "search space"],
        "related": ["emerson-running-key", "english-scorer-controls"],
        "scope": {
            "pages": plan["targets"],
            "artifacts": [PREFIX + "plan.json", PREFIX + "english-key-gp-control-plan.json"],
            "representation": "2,892 canonical GP29 rune indices from eight established readings in manuscript order; 55 nonempty LP2-00–55 ciphertext pages.",
            "procedure": "At every fitting contiguous source offset, add or subtract one key index per rune modulo 29 and score the entire page with the pinned English quadgram model. Compare the global best to 16 whole-key shuffled full-grid maxima. A separate post-observation diagnostic searches four disjoint 2,892-GP-rune windows of preserved Emerson English.",
            "parameters": "55 complete pages; 292,318 observed page/offset/sign alignments, 16 complete shuffled-key grids (seeds 33017100–33017115), both arithmetic signs, four post-observation English GP-key windows.",
            "exclusions": "Other source orders, substrings of pages, wrapping, key skips, word resets, alternate languages or score models, source text variants and any claim of general running-key exclusion."
        },
        "review": {"reviewer": "Portable producer with separately implemented compiled numeric full-grid checker and planted full-reading control", "retested_on": "2026-10-23", "kind": "computational", "human_review": "pending"},
        "reproduction": {
            "command": "python experiments/records/solved-reading-running-key/run.py --check && python experiments/records/solved-reading-running-key/fast_check.py && python experiments/records/solved-reading-running-key/english_key_control.py",
            "environment": "Python 3 standard library for portable producer; NumPy and Numba optional for fast independent full-grid check and English-source diagnostic. Run offline from repository root.",
            "script": PREFIX + "run.py",
            "script_sha256": item(PREFIX + "run.py")["sha256"],
            "inputs": [item(path) for path in input_paths],
            "outputs": [item(path) for path in output_paths]
        },
        "sources": [
            {"label": "Archived manuscript readings and source traces", "url": "https://jelliottdev.github.io/#/wiki/known-readings"},
            {"label": "Preserved Emerson source and book-cipher context", "url": "https://jelliottdev.github.io/#/wiki/emerson-self-reliance"},
            {"label": "English score calibration", "url": "https://jelliottdev.github.io/#/experiments/english-scorer-controls"}
        ],
        "visuals": [{"path": PREFIX + "key-comparison.svg", "caption": "The observed short-page score exceeds limited shuffled and unrelated-English comparison groups, but gives no readable page."}]
    }
    (HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    make()
