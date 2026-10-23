"""Freeze source bytes for a G-02 signature-verification replay.

This enumerates committed Git objects, not the potentially edited sparse checkout.
It does not verify any message or inspect the source verdicts.
"""

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT.parent / "source-cache" / "dukotah-cicada3301"
REV = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
SCRIPT = "liber-primus/analysis/round18/L8-provenance/verify_all_signatures.py"
TABLE = "liber-primus/analysis/round18/L8-provenance/PGP-VERIFICATION-TABLE.json"


def git(*args):
    return subprocess.run(["git", *args], cwd=SOURCE, check=True,
                          capture_output=True).stdout


def blob(path):
    return git("show", f"{REV}:{path}")


def main():
    tree = git("ls-tree", "-r", "-l", REV).decode().splitlines()
    paths = []
    for line in tree:
        head, path = line.split("\t", 1)
        if path.lower().endswith(".asc"):
            mode, kind, oid, size = head.split()
            assert kind == "blob"
            paths.append({"path": path, "git_object": oid, "bytes": int(size)})
    assert len(paths) == 135
    plan = {
        "schema": "liberpedia-g02-pgp-frozen-plan-v1",
        "source_revision": REV,
        "source_program": {"path": SCRIPT, "sha256": hashlib.sha256(blob(SCRIPT)).hexdigest()},
        "source_table": {"path": TABLE, "sha256": hashlib.sha256(blob(TABLE)).hexdigest()},
        "canonical_fingerprint": "6D854CD7933322A601C3286D181F01E57A35090F",
        "cases": paths,
        "controls": [
            "C1: an unchanged corpus signature verifies against the isolated canonical key",
            "C2: one body-character mutation fails the signature",
            "C3: a foreign-key signature does not verify as the canonical key",
            "C4: the signature-packet creation time survives C2 tampering",
        ],
        "comparison": "Verify every committed .asc with the pinned source program and independently compare per-path SHA-256, verdict, key fingerprint, and available signature time to the archived table; source-generated timestamps and GnuPG version are not expected to match.",
        "scope": "Pinned repository's 135 .asc paths, not every Cicada message ever published. No manuscript decryption claim.",
    }
    out = HERE / "plan-frozen.json"
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out, hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
