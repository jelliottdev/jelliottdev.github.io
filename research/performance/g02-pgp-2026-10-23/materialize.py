"""Materialize the frozen Git blobs into an isolated G-02 replay tree."""

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT.parent / "source-cache" / "dukotah-cicada3301"
TARGET = ROOT.parent / "g02-pgp-replay-20261023"
PLAN = json.loads((HERE / "plan-frozen.json").read_text(encoding="utf-8"))


def blob(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=SOURCE,
                          check=True, capture_output=True).stdout


def main():
    rev = PLAN["source_revision"]
    paths = [*PLAN["cases"], PLAN["source_program"]]
    for item in paths:
        data = blob(rev, item["path"])
        if "bytes" in item:
            assert len(data) == item["bytes"], item["path"]
        if "sha256" in item:
            assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
        dest = TARGET / item["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    manifest = {
        "source_revision": rev,
        "plan_sha256": hashlib.sha256((HERE / "plan-frozen.json").read_bytes()).hexdigest(),
        "files_materialized": len(paths),
        "bytes_materialized": sum(x["bytes"] for x in PLAN["cases"]) + len(blob(rev, PLAN["source_program"]["path"])),
    }
    dest = HERE / "materialize-receipt.json"
    dest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
