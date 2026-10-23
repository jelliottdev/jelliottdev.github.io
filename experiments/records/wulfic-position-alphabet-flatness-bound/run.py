"""Verify the bundled Stage T replay without an external checkout."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from check import verify

HERE = Path(__file__).resolve().parent


def main() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        assert hashlib.sha256((HERE / Path(item["path"]).name).read_bytes()).hexdigest() == item["sha256"]
    actual = verify()
    output = HERE / "results.json"
    expected = json.dumps(actual, ensure_ascii=False, indent=2) + "\n"
    if sys.argv[1:] == ["--check"]:
        assert output.read_text(encoding="utf-8") == expected
        print("Stage T source gates, manuscript counts and pooled boundary: OK")
    elif not sys.argv[1:]:
        output.write_text(expected, encoding="utf-8", newline="\n")
    else:
        raise SystemExit("Usage: run.py [--check]")


if __name__ == "__main__":
    main()
