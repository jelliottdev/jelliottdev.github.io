"""Verify the bundled Stage X2 result without the external source checkout."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    if sys.argv[1:] != ["--check"]:
        raise SystemExit("Usage: python experiments/records/wulfic-grid-periodic-byte-invariant/run.py --check")
    from check import check
    check()
    import plot
    assert (HERE / "comparison.svg").read_text(encoding="utf-8") == plot.render()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    print("Bundled Stage X2 replay: OK")


if __name__ == "__main__":
    main()
