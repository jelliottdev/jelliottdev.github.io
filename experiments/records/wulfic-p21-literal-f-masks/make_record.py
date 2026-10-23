"""Write scoped record metadata with current artifact hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/wulfic-p21-literal-f-masks/"


def item(name: str) -> dict:
    return {"path": PREFIX + name, "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()}


def main() -> None:
    pages = [f"lp2-{i:02d}" for i in range(4, 14)]
    record = {
      "id": "wulfic-p21-literal-f-masks",
      "status": "draft",
      "title": "Literal-F mask search on ten LP2 pages",
      "question": "Does the pinned second-layer program find any fixed-key F-skip mask that satisfies all its singleton I/A constraints?",
      "reader_question": "Can treating selected F runes as literal fix these keyword decodes?",
      "summary": "None of 27,402 source-defined F masks across ten exact pages passes all one-rune-word checks; the program falls back to choosing a mask by frequency score.",
      "finding": "Exact pinned Wulfic pages 21–30 align to LP2-04–13. The unmodified source enumerates 27,402 literal-F masks, with zero masks satisfying all of its singleton I/A constraints on every page. Its 45 fixed second-layer rune routes per page on the unmasked decode also print zero gate-passing rows. Nineteen whole-selection shuffled searches likewise have zero gated pages, showing this gate is nonselective under the stated control.",
      "limitations": "The source keyword parser drops V in DIVINITY and contracts EO in DEOR; this replay preserves its actual arrays. The source's narrow singleton separator rule and IoC/bigram score are not a general reading test. The 19 shuffles are a coarse descriptive reference, not a cipher model. Other keys, page ranges, interruption rules or downstream layers are not tested.",
      "next_steps": "Specify a corrected key/parser and a held-out passage test before treating an increased IoC from a selected mask as a decoding lead.",
      "outcome": "not-supported",
      "tags": ["LP2", "source replay", "F skip", "Vigenere", "singleton words", "selection effect"],
      "scope": {
        "pages": pages,
        "artifacts": [PREFIX + "plan.json"],
        "representation": "Exact source Git-object rune files pages/page_21–30, rune-aligned to current LP2-04–13; the source's word separators and keyword parser.",
        "procedure": "For each fixed page keyword/mode, enumerate every subset of ciphertext F positions as literal, non-advancing key slots. Apply the original all-singleton I/A gate, source score or fallback IoC rank, and source-defined unmasked second-layer routes. Run 19 complete page-shuffle controls.",
        "parameters": "Ten pages, 1–14 F positions each, 27,402 total source masks, 45 fixed rune routes per page, 19 pagewise shuffle repeats, seed 20261023.",
        "exclusions": "Corrected keyword parse, alternate F behavior, source pages outside 21–30, word-boundary variants, other languages and uncalled prime permutation helper."
      },
      "review": {
        "kind": "complete source-defined F-mask replay and selected-search control",
        "retested_on": "2026-10-23",
        "reviewer": "Ten Git-object/page alignments, two-pause planted recovery, 48 scalar/source parity cases, unmodified source output receipt, independent enumeration of all 27,402 observed masks and one shuffled full grid",
        "human_review": "pending"
      },
      "reproduction": {
        "command": "python experiments/records/wulfic-p21-literal-f-masks/check.py",
        "environment": "Python 3, NumPy and Numba. The full run, source parity and input snapshot also require a checkout of pinned Wulfic commit bf89d3d13aad2b8f2c95ab195cf1b092f250775c.",
        "script": PREFIX + "check.py",
        "script_sha256": item("check.py")["sha256"],
        "inputs": [item(name) for name in ("plan.json", "snapshot_inputs.py", "gate.py", "engine.py", "run.py", "check.py", "plot.py", "make_record.py", "article.md")],
        "outputs": [item(name) for name in ("inputs.json", "gate.json", "results.json", "source-run.json", "comparison.svg")]
      },
      "visuals": [{"path": PREFIX + "comparison.svg", "caption": "Selected F masks can raise IoC on each page, but none passes the source's all-singleton I/A gate."}],
      "sources": [
        {"label": "Pinned Wulfic second-layer program", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p21_30_second_layer.py"},
        {"label": "Pinned legacy input warning", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md"}
      ],
      "related": ["wulfic-prime-keyword-stream-families", "wulfic-keyed-transposition-cohort", "wulfic-systematic-stream-source"]
    }
    (HERE / "record.json").write_bytes(json.dumps(record, ensure_ascii=False, indent=2).encode("utf8") + b"\n")


if __name__ == "__main__":
    main()
