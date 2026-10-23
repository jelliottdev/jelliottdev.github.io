"""Optional exact Stage S dependency and Stage W source replay.

Usage: python experiments/records/wulfic-position-alphabet-long-keys/replay_source.py PATH_TO_WULFIC_CLONE
The original source remains in its repository; only output paths are redirected.
"""
from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
PINNED = {
    "tools/run_stage_s.py": "6ea9b7383b289b4f07f687d5346fe016ee49c4bb30169cf67a8b311e2b2c4e91",
    "tools/run_stage_w.py": "5df84192f29e141a1e310854a9de009151ab3b5efec39cc28fc23defe504b064",
    "tools/lpcore/alphabets.py": "64917029b624639bd84b7f3ee0a448254b80fdf25678c939f7961e68b269ff0b",
    "data/canonical/liber_primus_master.txt": "df7eaaa0c92243946803a7a90a7bfdcb36c0eba73f964f3a093c238ab01a5746",
    "data/canonical/liber_primus_translation.txt": "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47",
    "data/outguess/wisdom_hint.txt": "7e5ec097728197f5c0dba0729980565658fba486965809ffa25e3910a31c385a",
    "data/outguess/page_17.bin": "cbf1ccddc6c4bb2fd96d449e0667eb5be6c2a542de4e0f43e7ca188df7f289b1",
    "data/outguess/page_21.bin": "21e26fbcfd0f8cc5706ca4228245854703efa143173b793066ab3a2577f40db3",
    "data/outguess/page_43.bin": "0a318b3e9e195fdea9e941b7b458ae9cddef5147eec646b6da231b7d6615fe43",
}
NAMES = ("hint raw", "hint-reversed raw", "page_17.bin raw", "page_21.bin raw", "page_43.bin raw")


def main(source: Path) -> None:
    source = source.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == COMMIT
    for rel, expected in PINNED.items():
        assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == expected, rel
    sys.path.insert(0, str(source))
    s = importlib.import_module("tools.run_stage_s")
    w = importlib.import_module("tools.run_stage_w")
    stats = importlib.import_module("tools.lpcore.stats")
    segments = [str(item) for item in stats.UNSOLVED_SEGMENTS] + ["7-15"]
    jobs = [(name, segment) for name in NAMES for segment in segments]
    with tempfile.TemporaryDirectory(prefix="liberpedia-stage-w-") as temporary:
        temp = Path(temporary)
        with ProcessPoolExecutor(max_workers=s.WORKERS, initializer=s._init_worker) as pool:
            rows = list(pool.map(s._decode, jobs))
        dependency = temp / "stage_s_candidates.tsv"
        s.write_tsv("key\talignment\tsegment\trunes\tphases\tbest_phase\tbest_phase_log_lr\tlog_mean_lr",
                    [f"{k}\t{a}\t{seg}\t{n}\t{ph}\t{b}\t{top:.2f}\t{value:.2f}"
                     for k, a, seg, n, ph, b, top, value in rows], dependency)
        assert dependency.read_bytes() == (HERE / "source-stage_s_dependency.tsv").read_bytes()
        w.STAGE_S_PATH = dependency
        w.CONTROLS_PATH = temp / "stage_w_controls.tsv"
        w.CANDIDATES_PATH = temp / "stage_w_candidates.tsv"
        assert w.main([]) == 0
        for local, output in (("source-stage_w_controls.tsv", w.CONTROLS_PATH),
                              ("source-stage_w_candidates.tsv", w.CANDIDATES_PATH)):
            assert output.read_bytes() == (HERE / local).read_bytes(), local
    print("Pinned source Stage S dependency and both Stage W tables reproduced byte-for-byte")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Pass the path to the pinned Wulfic checkout")
    main(Path(sys.argv[1]))
