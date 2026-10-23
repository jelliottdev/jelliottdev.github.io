"""Re-run the pinned Round 16 PRNG screen in its preserved source layout."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import shutil
import tempfile

from check import verify

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "analysis" / "round16" / "prng" / "prng_sweep.py"


def main() -> None:
    # The upstream program writes a result containing elapsed time. Run in an
    # isolated copy so replaying never overwrites the archived evidence bytes.
    with tempfile.TemporaryDirectory(prefix="liberpedia-prng-") as folder:
        root = Path(folder) / "source"
        shutil.copytree(HERE / "source", root)
        script = root / "analysis/round16/prng/prng_sweep.py"
        subprocess.run([sys.executable, str(script)], check=True, cwd=root)
        print(verify(script.parent / "results.json"))


if __name__ == "__main__":
    main()
