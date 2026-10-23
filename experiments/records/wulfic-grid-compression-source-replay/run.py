"""Rebuild or verify the Stage X4 independent report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from check import audit

HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = json.dumps(audit(), ensure_ascii=False, indent=2) + "\n"
    path = HERE / "results.json"
    if args.check:
        assert path.read_text(encoding="utf-8") == content
        print("Stage X4 decoder replay: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
        print("Stage X4 decoder report written")


if __name__ == "__main__":
    main()
