"""Refresh only this draft record's declared hashes after its checks pass."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ID = HERE.name


def hashed(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["candidate_count"] == 6380
    assert result["model_control"]["all_selected_plants_exact"]
    assert result["null_trials"] == 199
    prefix = f"experiments/records/{ID}/"
    checks = [prefix + name for name in ("plan.json", "make_plan.py", "check.py", "plot.py", "make_record.py")]
    checks += [item["path"] for item in plan["inputs"]]
    checks += [f"data/pages/{page}.json" for page in plan["targets"]]
    unique_checks = list(dict.fromkeys(checks))
    record = {
        "id": ID,
        "status": "draft",
        "title": "GP prime values as a plaintext autokey",
        "question": "Do page-local plaintext-rune GP prime values, used one step back or as a running sum, yield unusually English-like complete LP2 pages?",
        "reader_question": "What happens if each decoded rune's prime value supplies the next key?",
        "summary": "Neither of two fixed plaintext-prime feedback rules stood out in a whole-page LP2 search: 144 of 199 matched shuffled searches scored at least as high as the best observed candidate.",
        "finding": "Across 6,380 complete-page candidates, the best score was −6.835 on LP2-32. In 144 of 199 page-shuffled full-grid controls, at least one candidate scored as high. All 116 arithmetic inversions and 12 full-length model-selection plants passed.",
        "limitations": "These two equations were defined for this bounded test, not supplied by the original proposal. The test does not define or test 'shedding,' word resets, skipped runes, across-page state, other languages or arbitrary gematria recurrences. A shuffled corpus is a conditional control, not a cipher model.",
        "next_steps": "A further numerical-autokey claim should specify its exact recurrence, initial state, reset points and literal state-discard rule before outputs are inspected, then test a full continuation against matched controls.",
        "outcome": "not-supported",
        "tags": ["gematria", "prime values", "plaintext autokey", "cumulative feedback", "GP29", "English quadgrams"],
        "related": ["cumulative-autokey-literal", "public-multihistory-feedback", "wulfic-autokey-seed-families", "feedback-opening-census", "crib-inferred-feedback-table", "solved-reading-running-key"],
        "scope": {
            "pages": plan["targets"],
            "artifacts": [prefix + "plan.json"],
            "representation": "12,956 GP29 rune indices across the 55 nonempty LP2-00–55 pages, ignoring punctuation and artwork; prime values from the canonical 29-rune alphabet.",
            "procedure": "Decode every whole page by either previous-plaintext-prime feedback or cumulative plaintext-prime-sum feedback; rank complete GP-to-Latin outputs under the pinned English quadgram model. Repeat the entire selection on 199 independently seeded within-page-shuffled corpora.",
            "parameters": "2 equations × 29 scalar seeds × 2 arithmetic signs × 55 pages = 6,380 observed candidates; 199 complete-grid shuffles, seeds 33017200–33017398. Page-local starts, one key advance per rune.",
            "exclusions": "Previous ciphertext-prime feedback (separate source W5), word-level prime sums, skips, word or line resets, cross-page state, additional key layers, other alphabets/languages, parable-specific reductions beyond the exhaustive seed residues and any unspecified iterative 'shedding' operation."
        },
        "review": {
            "reviewer": "Independent standard-library decoder and counted-quadgram replay against separate page JSON, 199 shuffle digests and three complete null grids",
            "retested_on": "2026-10-23", "kind": "computational", "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {prefix}run.py --check && python {prefix}check.py",
            "environment": "Python 3 with NumPy and Numba for the complete producer; independent checker uses Python 3 standard library. Offline from the repository root or complete experiment bundle.",
            "script": prefix + "run.py",
            "script_sha256": hashed(prefix + "run.py")["sha256"],
            "inputs": [hashed(path) for path in unique_checks],
            "outputs": [hashed(prefix + name) for name in ("results.json", "cases.csv", "feedback-overview.svg")]
        },
        "sources": [
            {"label": "Gematria Primus alphabet and prime values", "url": "https://jelliottdev.github.io/#/alphabet"},
            {"label": "Manuscript page index", "url": "https://jelliottdev.github.io/#/manuscript"},
            {"label": "English scorer controls", "url": "https://jelliottdev.github.io/#/experiments/english-scorer-controls"}
        ],
        "visuals": [{"path": prefix + "feedback-overview.svg",
                     "caption": "Both fixed plaintext-prime rules were searched; 144 of 199 matched full-grid shuffles scored at least as high as the LP2 winner."}]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
