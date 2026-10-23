"""Pin Stage N's manuscript grid and source-derived numerical inputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    paths = [BASE + "source-stage_n_results.tsv", BASE + "source-profile.json", "exports/alphanumeric-grids.csv"]
    plan = {
        "schema": "liberpedia-wulfic-grid-native-keys-plan-v1",
        "source": {
            "repository": "https://github.com/Wulfic/Cicada3301-Liber_Primus",
            "commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
            "stage_n_script_sha256": "b3445d5e04eea89865898f8eafa40b2d5abd7948fb1f4e1b2b667a63a5f1a5c4",
            "source_master_sha256": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
            "source_translation_sha256": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
            "profile": "Numerical input arrays exported from the pinned checkout; external source code itself is linked and not bundled."
        },
        "scope": {
            "grid": "The 256 LP2-49–51 printed tokens in their 32×8 row order, converted with the declared base-60 digit alphabet; reverse order is the only alternate byte route.",
            "byte_grid": "12 specified finite/repeated key streams × xor/subtract/add mod256 × forward/reversed grid =72 rows. At least90% printable bytes or one of the exact source offset-zero signatures passes.",
            "rune_grid": "Grid bytes mod29 and individual base-60 digits mod29, each forward/reversed; three GP29 directions, 29 constant shifts or three specified rune keys =384 rows. Pass at drift-tolerant source log LR≥30.",
            "source_controls": "Stage N itself did not have a planted detector-control gate. Checker-supplied synthetic positive cases are explicitly post-replay diagnostics, not prospective evidence about power for LP2."
        },
        "inputs": [{"path": path, "sha256": sha(ROOT / path)} for path in paths]
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
