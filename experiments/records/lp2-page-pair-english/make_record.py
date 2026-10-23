"""Freeze experiment publication metadata after all checks pass."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/lp2-page-pair-english"
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def pin(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


record = {
    "id": "lp2-page-pair-english",
    "status": "draft",
    "title": "Can one LP2 page decode another?",
    "question": "Do zero-offset addition or subtraction streams of two ciphertext pages yield English-like GP labels?",
    "reader_question": "Have we tried using another LP2 page as the key?",
    "summary": "A complete 4,455-stream zero-offset page-pair arithmetic search found no English score above matched whole-grid shuffled-page controls.",
    "finding": "The best eligible stream is LP2-18 minus LP2-02 (201 runes; score −6.802). In 193 of 256 conditional page-shuffle full searches, the best pair and operation scored at least as high (global add-one 194/257≈0.755).",
    "limitations": "Only direct zero-offset, nonrepeating A+B, A−B and B−A modulo 29 with English scoring were tested. Shifts, repeats, other layers, other languages and clue-selected pairings remain untested. The catalog is an idea list, not proof of a historical attempt.",
    "next_steps": "A more specific page-as-key theory should predeclare the page pair, alignment and key-advancement rule, then predict a continuous independently checkable reading.",
    "outcome": "not-supported",
    "tags": ["page as key", "page pairs", "additive cipher", "subtractive cipher", "GP29", "English scorer", "search space"],
    "related": ["lp2-page-pair-alignment", "english-scorer-controls"],
    "scope": {
        "pages": plan["targets"],
        "artifacts": [f"{PREFIX}/plan.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"],
        "representation": "Canonical GP29 rune indices, including headings, from all 55 rune-bearing LP2-00–55 text transcriptions; independent check re-parses structured page JSON.",
        "procedure": "Align every unordered page pair at rune zero to the shorter length. Compute A+B, A−B, and B−A modulo 29; score GP Latin labels with a fixed English quadgram model. Compare best eligible stream to 256 maxima of complete shared conditional-band page-shuffle searches.",
        "parameters": "1,485 pairs × three operations = 4,455 streams, of which 4,136 have ≥100 Latin quadgrams. Each of 256 controls uses Random(33017127+t). Three synthetic planted English outputs check exact arithmetic recovery and the scorer.",
        "exclusions": "Offsets, reverse streams, repeated page keys, other operations, changed page order or transcription, later decryption layers, non-English output and historical-negative claims."
    },
    "review": {
        "reviewer": "Independent structured-page JSON and separate rolling quadgram complete-grid replay; three planted GP reading controls",
        "retested_on": "2026-10-23",
        "kind": "computational",
        "human_review": "pending"
    },
    "reproduction": {
        "command": f"python {PREFIX}/run.py --check && python {PREFIX}/check.py",
        "environment": "Python 3, NumPy and Numba; offline from repository root or extracted experiment ZIP.",
        "script": f"{PREFIX}/run.py",
        "script_sha256": pin(f"{PREFIX}/run.py")["sha256"],
        "inputs": [pin(f"{PREFIX}/{name}") for name in ("plan.json", "make_plan.py", "check.py", "make_record.py")]
                  + [pin(row["path"]) for row in plan["inputs"]]
                  + [pin(f"data/pages/{page}.json") for page in plan["targets"]],
        "outputs": [pin(f"{PREFIX}/{name}") for name in ("results.json", "pair-scores.svg")]
    },
    "sources": [
        {"label": "User-supplied solution-idea catalog, item 7.3", "url": "https://github.com/jelliottdev/jelliottdev.github.io/blob/main/research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"},
        {"label": "CicadaSolvers manuscript transcription repository", "url": "https://github.com/CicadaSolvers/CicadaSolvers.github.io"},
        {"label": "Earlier page-pair IoC test", "url": "https://jelliottdev.github.io/#/experiments/lp2-page-pair-alignment"}
    ],
    "visuals": [{"path": f"{PREFIX}/pair-scores.svg", "caption": "The strongest zero-offset subtraction output and its English score against complete shuffled searches."}]
}

(HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
