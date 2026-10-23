"""Replay the full source KDF grid in a temp copy, preserving archived outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from check import verify, verify_k1_console

HERE = Path(__file__).resolve().parent


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="liberpedia-kdf-") as folder:
        root = Path(folder) / "source"
        shutil.copytree(HERE / "source", root)
        lp = root / "liber-primus"
        script = lp / "analysis/round15/KDF/sweep.py"
        d3 = lp / "analysis/round12/D3"
        baseline = json.loads((d3 / "original_results.json").read_text(encoding="utf-8"))
        live = subprocess.run([sys.executable, str(d3 / "pc_derivedkey.py")],
                              check=True, cwd=lp, capture_output=True, text=True)
        verify_k1_console(live.stdout, baseline["positive_control"])
        # The pinned sweep expects D3/results.json, but pc_derivedkey.py only
        # prints its values. Seed the exact archived file *after* independently
        # checking the live control, so K1 cannot pass on stale JSON alone.
        shutil.copyfile(d3 / "original_results.json", d3 / "results.json")
        # The pinned Round 16 report ran the K1 and K2 gates plus Stage A. Its
        # default B/C flags were not part of that result. Process count changes
        # throughput only; it does not narrow the finite hypothesis grid.
        subprocess.run([sys.executable, str(script), "--stages", "K1,K2,A",
                        "--nproc", "8"], check=True, cwd=lp)
        print(json.dumps(verify(lp), indent=2))


if __name__ == "__main__":
    main()
