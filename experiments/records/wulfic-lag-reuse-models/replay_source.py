"""Amended-source replay of pinned Wulfic Stages AC and AD.

Only the one-row control allocation is corrected in memory. All source
controls, full LP2/null scans, thresholds and result writers otherwise run
unaltered. This requires the separately pinned source checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

PIN = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
SOURCE_DIGESTS = {
    "tools/run_stage_ac.py": "1bf714c5d4f60e4b75ef297cad19cee58f99744fce6d3eaead6417828a2359ef",
    "tools/run_stage_ad.py": "e530fe6673dcceacb515201e96bbe9cb4cd318746df188e76f5d2e6a45fec04c",
}
TABLE_DIGESTS = {
    "ac_lags": "2ee19b3ed300186514ad7a5f89ad2642dff98a27724fc5d2d18f02a5f6392402",
    "ac_top": "ade114aa042496045505091a2f0eefaeb589e4609abc9a156bf1ed9e1b1a0f12",
    "ac_controls": "7f114a2aaf7a424910d5d4c919a911c0913759e05095bcb4588c5aeafb666405",
    "ad_lags": "3c45d6dab3cc5fbaf86d41298734c53c79d1fcb4abd25e52c19b5b78b1aed927",
    "ad_top": "dc0ef34df7d0473b35f590aabf1e153e7f23d68ea7f3338734785c654327c020",
    "ad_controls": "b09a994463a110ccf8e216624401b9e3dd7c4f62856c0b27428bd8cabc045ada",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def shape_corrected(table: np.ndarray, x: np.ndarray):
    cs = np.zeros((table.shape[0], len(x) + 1))
    np.cumsum(table[:, x], axis=1, out=cs[:, 1:])
    return cs[:, -1].copy(), (cs - np.minimum.accumulate(cs, axis=1)).max(axis=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", choices=("ac", "ad", "both"), default="both")
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() != PIN:
        raise AssertionError("Pinned source revision mismatch")
    for name, digest in SOURCE_DIGESTS.items():
        if sha((source / name).read_bytes()) != digest:
            raise AssertionError(f"Pinned source bytes changed: {name}")
    sys.path.insert(0, str(source))
    from tools import run_stage_ac as ac, run_stage_ad as ad
    try:
        ac.segment_stats(np.zeros((1, 29)), np.array([0, 1]))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected source control-shape defect is absent")
    ac.segment_stats = shape_corrected
    ad.segment_stats = shape_corrected
    results = {}
    for name, module in (("ac", ac), ("ad", ad)):
        if args.stage not in ("both", name):
            continue
        for kind in ("lags", "top", "controls"):
            setattr(module, kind.upper() + "_PATH", output / f"stage_{name}_{kind}.tsv")
        start = time.perf_counter()
        status = module.main([])
        elapsed = time.perf_counter() - start
        checks = {}
        for kind in ("lags", "top", "controls"):
            label = f"{name}_{kind}"
            generated = (output / f"stage_{label}.tsv").read_bytes()
            original = subprocess.check_output(
                ["git", "show", f"HEAD:reference/findings/stage_{label}.tsv"], cwd=source
            )
            if sha(original) != TABLE_DIGESTS[label]:
                raise AssertionError(f"Pinned source table hash changed: {label}")
            if generated != original:
                raise AssertionError((label, "full source result mismatch", sha(generated), sha(original)))
            checks[kind] = {"sha256": sha(generated), "bytes": len(generated),
                            "rows": generated.count(b"\n") - 1}
        results[name] = {"source_return_code": status, "elapsed_seconds": elapsed,
                         "tables": checks}
        (output / f"replay_{name}.json").write_text(json.dumps(results[name], indent=2) + "\n",
                                                       encoding="utf-8", newline="\n")
        print(f"PASS {name.upper()}: source return {status}, all three output TSVs byte-identical; {elapsed:.1f}s", flush=True)
    (output / "replay_results.json").write_text(json.dumps(results, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
