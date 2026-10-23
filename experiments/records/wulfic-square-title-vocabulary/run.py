"""Check all 30 source title outputs against independent site-text arithmetic."""
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
        path = HERE / Path(item["path"]).name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    text = json.dumps(verify(), ensure_ascii=False, indent=2) + "\n"
    output = HERE / "results.json"
    if sys.argv[1:] == ["--check"]:
        assert output.read_text(encoding="utf-8") == text
        print("Stage I title: all 30 fixed complete decodes and source null summary OK")
    elif not sys.argv[1:]:
        output.write_text(text, encoding="utf-8", newline="\n")
    else:
        raise SystemExit("Usage: run.py [--check]")


if __name__ == "__main__":
    main()
