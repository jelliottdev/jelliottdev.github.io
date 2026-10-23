"""Copy the six pinned AC/AD source tables by exact Git object bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source, text=True).strip() != plan["source"]["commit"]:
        raise AssertionError("Pinned source revision mismatch")
    for stage in ("ac", "ad"):
        for kind in ("lags", "top", "controls"):
            name = f"stage_{stage}_{kind}.tsv"
            data = subprocess.check_output(["git", "show", "HEAD:reference/findings/" + name], cwd=args.source)
            digest = plan["source"][f"published_{stage}_{kind}_sha256"]
            if hashlib.sha256(data).hexdigest() != digest:
                raise AssertionError(f"Pinned source bytes changed: {name}")
            (HERE / f"source-{name}").write_bytes(data)
    print("PASS: all six source table bytes pinned")


if __name__ == "__main__":
    main()
