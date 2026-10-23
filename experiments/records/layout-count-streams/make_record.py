"""Freeze publication metadata after the independent replay passes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/layout-count-streams"
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def file_entry(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


record = {
    "id": "layout-count-streams",
    "status": "draft",
    "title": "Do line or word lengths carry a message?",
    "question": "Do the ordered rune counts per physical line or visible word produce direct English as GP symbols?",
    "reader_question": "Have we tried reading the line and word lengths as a message?",
    "summary": "Eight direct GP readings of manuscript line and word lengths did not stand out against matched shuffled-count searches.",
    "finding": "The best reading used visible-word rune count minus one with page-local scoring (−6.697). In 78 of 256 matched shuffled-count searches, the best of the same eight readings scored at least as high (global add-one 79/257≈0.307).",
    "limitations": "Only direct English under count or count-minus-one GP-index mappings and the stated line/word boundaries was tested. A further cipher, other numeral mapping or visual layout signal remains open. The source catalog lists an idea, not a verified historical attempt.",
    "next_steps": "Any more specific count theory should predeclare its counting convention, numeral mapping and cipher layer, then predict a continuous independently checkable reading.",
    "outcome": "not-supported",
    "tags": ["line lengths", "word lengths", "layout counts", "GP29", "number encoding", "English scorer", "search space"],
    "related": ["line-initial-layout-control", "corpus-prefix-census", "rail-fence-visible-words", "english-scorer-controls"],
    "scope": {
        "pages": plan["targets"],
        "artifacts": [f"{PREFIX}/plan.json", "research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"],
        "representation": "Physical rune-bearing line counts and hyphen-delimited visible-word rune counts from all 55 rune-bearing LP2-00–55 transcription pages.",
        "procedure": "Compute 594 line and 2,776 word counts; interpret each as n mod29 or (n−1) mod29, score canonical GP Latin labels page-locally or joined. Compare the best of eight scores with best-of-eight maxima in 256 shared within-page count shuffles. Plant decoded GP readings in synthetic count streams.",
        "parameters": "Eight declared readings; 256 shared shuffles seeded 33017125–33017380. Every arm clears the frozen 100-English-quadgram eligibility gate.",
        "exclusions": "Other separators or transcription variants, enciphered or non-English count streams, visual spacing in source images, alternate numeral encodings and historical-attempt claims."
    },
    "review": {
        "reviewer": "Independent page-JSON count parser and Counter-based four-letter scorer complete-grid replay; eight planted known-reading controls",
        "retested_on": "2026-10-23",
        "kind": "computational",
        "human_review": "pending"
    },
    "reproduction": {
        "command": f"python {PREFIX}/run.py --check && python {PREFIX}/check.py",
        "environment": "Python 3 standard library; offline from repository root or extracted experiment ZIP.",
        "script": f"{PREFIX}/run.py",
        "script_sha256": file_entry(f"{PREFIX}/run.py")["sha256"],
        "inputs": [file_entry(f"{PREFIX}/{name}") for name in ("plan.json", "make_plan.py", "check.py", "make_record.py")]
                  + [file_entry(row["path"]) for row in plan["inputs"]],
        "outputs": [file_entry(f"{PREFIX}/{name}") for name in ("results.json", "count-stream.svg")]
    },
    "sources": [
        {"label": "User-supplied solution-idea catalog, item 9.10", "url": "https://github.com/jelliottdev/jelliottdev.github.io/blob/main/research/source-archive/lp2-collected-solution-ideas-2026-10-23.txt"},
        {"label": "CicadaSolvers manuscript transcription repository", "url": "https://github.com/CicadaSolvers/CicadaSolvers.github.io"},
        {"label": "English scorer calibration", "url": "https://jelliottdev.github.io/#/experiments/english-scorer-controls"}
    ],
    "visuals": [{"path": f"{PREFIX}/count-stream.svg", "caption": "A direct word-count mapping in the first six LP2-00 words and the best eight-way score against 256 shuffled searches."}]
}

(HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
