"""Replay all 34 source L2 cells in a temporary copy and check the result."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from optimized import run

HERE = Path(__file__).resolve().parent
LANE = Path("analysis/round21/L2-nskips-crossover-length")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="liberpedia-nskips-") as folder:
        root = Path(folder) / "source"
        shutil.copytree(HERE / "source", root)
        lp = root / "liber-primus"
        result = lp / LANE / "nskips_crossover.json"
        result.unlink(missing_ok=True)
        print(json.dumps(run(lp), indent=2))


if __name__ == "__main__":
    main()
