"""Write draft metadata with exact local input and output hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ID = HERE.name
BASE = f"experiments/records/{ID}/"


def hashed(rel: str) -> dict[str, str]:
    return {"path": rel, "sha256": hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()}


def main() -> None:
    rec = {
        "id": ID,
        "status": "draft",
        "title": "What separates LP2’s surviving doublets?",
        "question": "Do six source-defined difference, boundary, periodic, clustering, key-switch or skip-next tests distinguish the 86 surviving LP2 doublets?",
        "reader_question": "Do the surviving repeated runes reveal how LP2 was encrypted?",
        "summary": "Pinned H/O source tests and independent pair-by-pair replay find no declared H concentration; two named key switches and a specific skip-next rule fail their source comparisons.",
        "finding": "All 16 selected H/O source assertions pass. The independent checker recreates 12,947 within-section pairs and all 86 doublets from site pages, then recalculates all 62 period/clock rows and remaining manuscript summaries. The strongest nonzero-difference z is −2.58, line breaks hold 4/585 repeats, best period p is 0.0355 versus 0.000161 corrected line, and nine-section p is 0.721. Two named key-switch constructions yield at most 10/2,898 repeats on solved text; the specified skip-next model has LP2 LLR −21.34 below its −10 line.",
        "limitations": "The source pairs join pages within nine sections, unlike the site's page-only 12,901-pair count. The H checks test chosen summaries and their declared selection rules, not all historical questions about doublets. H5 extrapolates from two named key pairs on solved text. O C14 assumes a 0.19 repeat parameter and solved-text difference profile. None decrypts LP2 or excludes arbitrary collision avoidance.",
        "next_steps": "A proposed doublet-avoidance generator should specify key sequence, collision response and boundary clock, then predict both LP2's residual doublet rate and another held-out feature.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "doublets", "key skipping", "line breaks", "periodicity"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE+"plan.json", BASE+"inputs.json"],
            "representation": "Source nine-section LP2-00–55 GP29 stream with written-line and page markers, 12,947 within-section adjacent pairs; site page text independently reconstructs all pair positions and marker flags.",
            "procedure": "Run unchanged source H and O unittest classes with synthetic controls; preserve source pair/control input ledger; independently rebuild pairs from site raw pages and recompute H L1–L5 plus O C14.",
            "parameters": "L1 28 residues, |z|=3.5; L2 line-break 2.5% rule; L3 31 periods×2 clocks and Bonferroni .01/62; L4 nine sections and 500-pair windows; L5 two named key pairs×ideal/literal switches; O fixed repeat .19 and LLR cutoff −10.",
            "exclusions": "Other pair-boundary conventions, unspecified or adaptive key switches, other skip rates/plaintext models, decoder outputs, later cipher layers and any mechanism lacking an independently testable output."
        },
        "review": {"kind": "exact pinned public-source H/O assertion replay and independent site-pair/numerical checker",
                   "retested_on": "2026-10-23", "reviewer": "16 selected source tests passed; every one of 12,947 pairs and all 62 period rows independently verified", "human_review": "pending"},
        "reproduction": {"command": f"python {BASE}check.py && python {BASE}plot.py --check",
                         "environment": "Python 3 standard library; optional unchanged source replay needs the pinned external Wulfic Git checkout.",
                         "script": BASE+"check.py", "script_sha256": hashed(BASE+"check.py")["sha256"],
                         "inputs": [hashed(BASE+n) for n in ("plan.json","inputs.json","replay_source.py","plot.py")]
                         + [hashed(f"data/pages/lp2-{i:02d}.json") for i in range(56)],
                         "outputs": [hashed(BASE+n) for n in ("results.json","distribution.svg","line-breaks.svg")]},
        "visuals": [{"path": BASE+"distribution.svg", "caption": "Every surviving equal-rune pair along the nine source sections."},
                    {"path": BASE+"line-breaks.svg", "caption": "Observed line-break and within-line repeat rates against the proposed line-end rule."}],
        "sources": [{"label": "Wulfic pinned H/O tests", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tests/test_leak.py"},
                    {"label": "Wulfic source doublet arithmetic", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/leak.py"}],
        "related": ["doublet-boundaries", "doublet-placement", "doublet-section-residues", "decoder-skip-controls"]
    }
    (HERE/"record.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
