"""Write the metadata and current file digests for this bounded source replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/wulfic-p20-prime-position-routes/"


def item(name: str) -> dict:
    return {"path": PREFIX + name, "sha256": hashlib.sha256((HERE / name).read_bytes()).hexdigest()}


def main() -> None:
    record = {
      "id": "wulfic-p20-prime-position-routes",
      "status": "draft",
      "title": "Prime-position route search on LP2-03",
      "question": "What does the pinned P20 prime-position split and 58-route search produce on its actual source page?",
      "reader_question": "Does the prime-position route give a reading?",
      "summary": "The strongest route has six source-style trigram hits; 57 of 199 complete rune-shuffle searches reach at least six.",
      "finding": "Pinned page_20 maps to LP2-03 with 217 runes, not the 646 claimed in the source comment. Its nonprime-position stream has 170 runes. The 11-column route leads the 58 executed routes with six source-style trigram hits, a score reached or exceeded by 57/199 complete shuffled searches. The original source reports ten routes under branch-specific filters but does not establish a readable passage.",
      "limitations": "The shuffle comparison is descriptive, not a cipher model. The source uses variable-width GP Runeglish, brief English trigram lists, and no validated full-passage criterion. Only source-retained routes passed an unmodified-script synthetic parity gate; all 58 saved manuscript routes have separate index-map reconstruction. Other pages, reading rules, languages and layouts are outside scope.",
      "next_steps": "Propose a route from independent page evidence and test a held-out passage under a fixed reading criterion.",
      "outcome": "inconclusive",
      "tags": ["LP2", "source replay", "prime positions", "transposition", "route cipher", "selection effect"],
      "scope": {
        "pages": ["lp2-03"],
        "artifacts": [PREFIX + "plan.json"],
        "representation": "Exact GP29 runes in Wulfic pages/page_20/runes.txt at commit bf89d3d, aligned to current LP2-03; source Runeglish output and committed Deor poem.",
        "procedure": "Partition by prime zero-based rune position, take the 170-rune nonprime stream, choose the source's first maximal-IoC Caesar shift, and execute its 58 literal routes and branch-specific trigram screens. Retain the separate prime rune-index-value split as an audit, then compare whole-search maximums with 199 seeded full-page rune shuffles.",
        "parameters": "One pinned source page; 29 Caesar shifts; 58 executed routes; 199 whole-search shuffles at seed 20261023.",
        "exclusions": "No broader transposition family search, new word segmentation, other page alignment or output language, and no claim of plaintext from a trigram count."
      },
      "review": {
        "kind": "pinned source replay with independently reconstructed route outputs",
        "retested_on": "2026-10-23",
        "reviewer": "Pre-outcome planted route recovery and pinned-source retained-route parity; independent 58-route digest and one complete shuffled-search reconstruction",
        "human_review": "pending"
      },
      "reproduction": {
        "command": "python experiments/records/wulfic-p20-prime-position-routes/check.py",
        "environment": "Python 3 and NumPy for the independent checker. Optional source-root checks and full rerun use a checkout of pinned Wulfic commit bf89d3d13aad2b8f2c95ab195cf1b092f250775c.",
        "script": PREFIX + "check.py",
        "script_sha256": item("check.py")["sha256"],
        "inputs": [item(name) for name in ("plan.json", "snapshot_inputs.py", "engine.py", "gate.py", "run.py", "check.py", "plot.py", "make_record.py", "article.md")],
        "outputs": [item(name) for name in ("inputs.json", "gate.json", "results.json", "source-run.json", "comparison.svg")]
      },
      "visuals": [{"path": PREFIX + "comparison.svg", "caption": "The best manuscript route scores six hits; 57 of 199 complete searches on shuffled runes score at least six."}],
      "sources": [
        {"label": "Pinned Wulfic route program", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/solve_p20.py"},
        {"label": "Pinned Wulfic source-input warning", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md"}
      ],
      "related": ["wulfic-deor-interlocking-streams", "wulfic-keyed-transposition-cohort", "lp2-row-column-routes"]
    }
    (HERE / "record.json").write_bytes(json.dumps(record, ensure_ascii=False, indent=2).encode("utf8") + b"\n")


if __name__ == "__main__":
    main()
