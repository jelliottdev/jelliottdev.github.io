"""Optional exact AA/Z source replay from the pinned external repository."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
PINNED = {
    "tools/run_stage_aa.py": "a15ee3ad1a4b7bba7fe0185f7f734c57fcd4d02dffe4557c97419cce0fbcf3b1",
    "tools/run_stage_z.py": "0dd32c394b50b6066bef16abfb21818ed61c8ca94ed47eb113446b00dad3a23a",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
    "data/corpora/emerson_essays.txt": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0",
}
NAMES = ["stage_aa_results.tsv", "stage_aa_verdicts.tsv", "stage_aa_controls.tsv",
         "stage_z_results.tsv", "stage_z_controls.tsv"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verify-output-dir", type=Path,
                        help="Validate completed full reruns without repeating them")
    args = parser.parse_args()
    root = args.source_dir.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == COMMIT
    for name, expected in PINNED.items():
        assert sha(root / name) == expected, name

    def verify(folder: Path) -> None:
        for name in NAMES:
            assert sha(folder / name) == sha(HERE / f"source-{name}"), name

    if args.verify_output_dir:
        verify(args.verify_output_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="liberpedia-wulfic-local-codebooks-") as directory:
            folder = Path(directory)
            for stage in ("aa", "z"):
                code = f"from pathlib import Path; import tools.run_stage_{stage} as m; p=Path(__import__('sys').argv[1]); "
                code += "m.RESULTS_PATH=p/'stage_%s_results.tsv'; m.CONTROLS_PATH=p/'stage_%s_controls.tsv'; " % (stage, stage)
                if stage == "aa":
                    code += "m.VERDICTS_PATH=p/'stage_aa_verdicts.tsv'; "
                code += "raise SystemExit(m.main([]))"
                subprocess.run([sys.executable, "-c", code, str(folder)], cwd=root, check=True)
            verify(folder)
    print("Pinned Stage AA/Z source outputs reproduced byte-for-byte: OK")
