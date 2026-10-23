"""Pin exact source tables and the independently parsed manuscript inputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    paths = [f"experiments/records/{HERE.name}/source-stage_{stage}_{kind}.tsv"
             for stage, kinds in (("aa", ("results", "verdicts", "controls")),
                                  ("z", ("results", "controls"))) for kind in kinds]
    paths += ["data/index.json"] + [f"data/pages/lp2-{page:02d}.json" for page in range(56)]
    plan = {
        "schema": "liberpedia-wulfic-local-codebook-plan-v1",
        "source": {
            "repository": "https://github.com/Wulfic/Cicada3301-Liber_Primus",
            "commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
            "stage_aa_script_sha256": "a15ee3ad1a4b7bba7fe0185f7f734c57fcd4d02dffe4557c97419cce0fbcf3b1",
            "stage_z_script_sha256": "0dd32c394b50b6066bef16abfb21818ed61c8ca94ed47eb113446b00dad3a23a",
            "master_sha256": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
            "translation_sha256": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
            "emerson_sha256": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0",
            "source_outputs": "Full AA and Z TSVs replayed byte-for-byte from the pinned source revision."
        },
        "hypotheses": {
            "AA": "A position-independent local mapping of a plaintext context retains equal-window n-grams at separated positions.",
            "Z": "An injective fixed word or aligned-block codebook retains equality of repeated source units."
        },
        "source_grid": {
            "AA": "Widths 0–12; n-grams 3–7; within-section and joined-stream modes. Ten LP2 n-gram statistics and 26 width verdicts, with 200 positive draws from each of two sources per width/n/mode.",
            "Z": "Two word-codebook cells and 70 aligned-block cells: n=2–8, all offsets 0–n−1, within-section and joined-stream modes.",
            "controls": "1,000 flat-null draws and 200 positive draws each from Emerson and solved LP1 for each declared cell; source anti-doublet model redraws 81% of adjacent collisions.",
            "seed": 3301,
            "interpretation": "EXCLUDED applies only when both positive sources separate from the null and LP2 falls below both lower bounds. UNTESTABLE is lack of control power, not a failed cipher."
        },
        "inputs": [{"path": name, "sha256": digest(ROOT / name)} for name in paths],
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
