"""Optional full Stage X2 source replay against a pinned external checkout.

Usage: python experiments/records/wulfic-grid-periodic-byte-invariant/replay_source.py PATH_TO_WULFIC_CLONE
The upstream source is not redistributed here. The 100,000-draw replay takes minutes.
"""
from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
PINNED = {
    "tools/run_stage_x.py": "29b1a75394a4a8b198531a52c185dac6e2a8f1661c01c2e19092a77c9a34eb1d",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
    "data/corpora/emerson_essays.txt": "a56d5bb419a8c28c4e0187a937c01991ea953817c036ee7f7f835ea2084c03a0",
}


def main(source: Path) -> None:
    source = source.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    assert commit == COMMIT, commit
    for rel, digest in PINNED.items():
        assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == digest, rel
    sys.path.insert(0, str(source))
    import numpy as np
    module = importlib.import_module("tools.run_stage_x")
    corpus = module.load_corpus()
    grid = np.array(module.keys.grid_bytes(corpus), dtype=np.uint8)
    assert grid.shape == (256,)
    controls = module.control_blocks(corpus, False)
    rows = module.x2_rows(grid, controls, module.NULL_DRAWS)
    with tempfile.TemporaryDirectory(prefix="liberpedia-stage-x2-") as temporary:
        output = Path(temporary) / "stage_x_periodic.tsv"
        module.write_tsv(output,
                         ("reading", "period", "pairs", "coincidences", "null_mean", "null_max",
                          "null_p_ge", "structure", *(f"q001_{k}" for k in module.CLASSES),
                          *(f"verdict_{k}" for k in module.CLASSES)), rows)
        assert output.read_bytes() == (HERE / "source-stage_x_periodic.tsv").read_bytes()
    print("Pinned source Stage X2: all 256 rows reproduced byte-for-byte")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Pass the path to the pinned Wulfic checkout")
    main(Path(sys.argv[1]))
