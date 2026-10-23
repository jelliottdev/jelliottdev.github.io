"""Check the bundled Stage W source replay without the external checkout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    if sys.argv[1:] != ["--check"]:
        raise SystemExit("Usage: python experiments/records/wulfic-position-alphabet-long-keys/run.py --check")
    from check import check
    check()
    import plot
    assert (HERE / "comparison.svg").read_text(encoding="utf-8") == plot.render()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["cell_count"] == 50 and result["control_count"] == 505
    print("Bundled Stage W source replay: OK")


if __name__ == "__main__":
    main()
