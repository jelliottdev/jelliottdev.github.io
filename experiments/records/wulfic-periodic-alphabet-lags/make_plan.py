"""Pin Stage AE and all independently recounted LP2 page inputs."""
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
    paths = [BASE + "source-stage_ae_lags.tsv", BASE + "source-stage_ae_controls.tsv", "data/index.json"]
    paths += [f"data/pages/lp2-{n:02d}.json" for n in range(56)]
    plan = {
        "schema": "liberpedia-wulfic-periodic-alphabet-plan-v1",
        "source": {
            "repository": "https://github.com/Wulfic/Cicada3301-Liber_Primus",
            "commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
            "stage_ae_script_sha256": "31e5fd74bd991cbbb08ea0dba46eba3d541afd75594b3b73204602a889da252f",
            "stage_ac_dependency_sha256": "1bf714c5d4f60e4b75ef297cad19cee58f99744fce6d3eaead6417828a2359ef",
            "source_master_sha256": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
            "source_translation_sha256": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
            "source_emerson_sha256": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0"
        },
        "scope": {
            "model": "A period-L key selects the same bijective alphabet at positions i and i+L, so equality of those ciphertext positions equals equality of their plaintext positions.",
            "targets": "All 12,935 integer lags L=11..12,945 on the joined 12,956-rune LP2 stream, sections 7–15.",
            "pass": "One-sided binomial upper tail against the manuscript's empirical rune collision p0, with family threshold 0.01/12,935.",
            "exclusion": "One-sided binomial lower tail under agreement probability 0.050 at most exp(-10).",
            "controls": "20 flat-null streams with 81% adjacent-collision redraw, and 10 periodic-tabula draws each from Emerson and solved LP1 at P=1033,1729,3301,6000,9000; source seed3301.",
            "source_status": "Full source run valid and both emitted TSVs byte-identical to pinned repository outputs."
        },
        "inputs": [{"path": name, "sha256": sha(ROOT / name)} for name in paths]
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
