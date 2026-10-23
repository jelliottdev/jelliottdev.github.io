"""Execute the pinned H-03 source function and a planted printable control."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "replay-plan.json").read_text(encoding="utf-8"))
SRC = HERE / "source/liber-primus/analysis/round16/zeroFP/zerofp_tests.py"


def call(mod):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        result = mod.h03_cookies_xor()
    return result, stdout.getvalue()


def main():
    for row in PLAN["source_files"]:
        p = HERE.parents[2] / row["path"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row["sha256"], p
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("pinned_zerofp_tests", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    source, stdout = call(mod)
    with tempfile.TemporaryDirectory(prefix="liberpedia-h03-plant-") as td:
        analysis = Path(td) / "analysis"
        shutil.copytree(HERE / "source/liber-primus/analysis", analysis)
        cookie = bytes.fromhex((analysis / "armada20/key_cookie167.txt").read_text().strip())
        assert len(cookie) == 32
        plaintext = b"PLANTED COOKIE XOR CONTROL PASS!"
        assert len(plaintext) == 32
        blob = analysis / "pp49_51/canon_256.bin"
        original = blob.read_bytes()
        blob.write_bytes(bytes(x ^ y for x, y in zip(cookie, plaintext)) + original[32:])
        previous = mod.ANALYSIS
        try:
            mod.ANALYSIS = analysis
            planted, plant_stdout = call(mod)
        finally:
            mod.ANALYSIS = previous
    assert any(x["cookie"] == "cookie167" and x["blob"] == "canon_256" and x["offset"] == 0
               for x in planted["hits"]), "planted source hit not recovered"
    output = {"source": source, "planted": planted, "source_stdout": stdout,
              "planted_stdout": plant_stdout, "plant_plaintext": plaintext.decode("ascii")}
    (HERE / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"source {source['trials']} cases: {source['verdict']}, max printable {source['max_printable']}; planted hit recovered")


if __name__ == "__main__":
    main()
