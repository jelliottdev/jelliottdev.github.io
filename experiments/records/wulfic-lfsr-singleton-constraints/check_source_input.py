"""Optional unchanged-source parser cross-check against the pinned Git tree."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True, help="checkout at bf89d3d13aad2b8f2c95ab195cf1b092f250775c")
    args = ap.parse_args()
    source = args.source.resolve()
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    assert revision == "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
    spec = importlib.util.spec_from_file_location("legacy_lfsr", source / "tools/legacy/lfsr_gf29_solver.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pages = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))["pages"]
    with tempfile.TemporaryDirectory() as folder:
        module.ROOT = Path(folder)
        for page in pages:
            lp2 = int(page["id"].split("-")[1])
            scan = lp2 + 17
            raw = subprocess.check_output(["git", "-C", str(source), "show", f"HEAD:pages/page_{scan:02d}/runes.txt"])
            path = module.ROOT / f"pages/page_{scan:02d}/runes.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            values, lengths = module.load_runes(scan)
            assert values == page["runes"]
            assert module.get_single_rune_positions(lengths) == page["singleton_positions"]
            print(page["id"], "source scan", scan, "runes", len(values), "singletons", len(page["singleton_positions"]))


if __name__ == "__main__":
    main()
