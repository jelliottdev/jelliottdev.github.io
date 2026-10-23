"""Regenerate the pinned inputs and arithmetic sanity checks in plan.json."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def build() -> dict:
    spec = importlib.util.spec_from_file_location("number_check", HERE / "check.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    paths = [
        "experiments/records/wulfic-stage-ab-reset-alphabets/layout.json",
        "experiments/records/wulfic-stage-ab-reset-alphabets/check.py",
        *(f"experiments/records/wulfic-number-key-streams/source-stage_{stage}_{kind}.tsv"
          for stage in ("ag", "ah") for kind in ("candidates", "controls")),
        "data/index.json",
        *(f"data/pages/lp2-{n:02d}.json" for n in range(56)),
    ]
    return {
        "schema": "liberpedia-wulfic-number-key-streams-plan-v1",
        "source": {
            "repository": "https://github.com/Wulfic/Cicada3301-Liber_Primus",
            "commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
            "stage_ag_program": "tools/run_stage_ag.py",
            "stage_ag_sha256": "46262fbf32c882fc3c6fef37937326e5cf27763e8aa430dafae338da25b6317b",
            "stage_ah_program": "tools/run_stage_ah.py",
            "stage_ah_sha256": "d6471ef1511252883a6813755a72a9e888712ecc06d4b449c56fa57d0c090a5d",
            "fastdetect_sha256": "b98c876e2963ac257164141f0100e5cf0e034070f16628816e2544ba493530d4",
            "detect_sha256": "fc0f0fb715e888f9ffe0ee434f786f273a0ee939ab050d54ff4e369a8f301eeb",
            "keys_sha256": "551f5c0c4746c934b2317b22562fd95db969600dda2bfbe2a3ab7c359255cafc",
            "ciphers_sha256": "80876bc3f4a9b22fdfeb459fcb6500ed1d4fe3ee346afc26ac04d38c3052c566",
            "source_master_sha256": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
            "source_translation_sha256": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
        },
        "manuscript": "12,956 GP29 runes, source sections 7–15; site transcription independently reconstructs these positions.",
        "streams": {
            "AG": ["pi", "e", "phi", "sqrt2", "sqrt3", "ln2", "sqrt3301",
                   "copeland-erdos", "champernowne", "prime-totients"],
            "AH": [f"{name} {form}" for name in ("totient", "sigma", "totient-sum",
                    "prime-gaps", "totient-of-totient", "n-times-totient")
                   for form in ("raw", "chain")],
        },
        "grid": {
            "alignments": [*map(str, range(7, 16)), "7-15"],
            "modes": ["sub", "add", "beaufort"],
            "shifts": list(range(29)),
            "possible_starts": 1000,
            "source_key_names": 22,
            "distinct_key_streams": 21,
            "candidate_rows": 19140,
            "model": "Source drift-tolerant log likelihood ratio: uniform 1,000-start marginalization; stay/skip 0.02, emission noise 0.1, solved LP1 unigram prior.",
        },
        "rule": "Pass if log LR >= 30. Exclude a stream/alignment/mode cell if controls pass and all 29 shifts score <= -10.",
        "controls": "Seed 3301; planted fresh/next stream-key encryptions and wrong random keys at 729 and 3,316 runes; positives >=30 and negatives <30.",
        "arithmetic_first_five": module.small_arithmetic_prefixes(),
        "caveat": "Section 10 contains only nine runes. No claim extends to untested transforms, starts, key sources or plaintext priors.",
        "inputs": [{"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                   for p in paths],
    }


if __name__ == "__main__":
    (HERE / "plan.json").write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
