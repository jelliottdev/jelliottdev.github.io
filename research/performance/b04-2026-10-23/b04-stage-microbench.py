"""Small synthetic, unchanged B04 harness timings. No LP2 pages are read."""
import json
import math
import pathlib
import sys
import time

import argparse

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument("--source-root", type=pathlib.Path, required=True)
_parser.add_argument("--output", type=pathlib.Path)
_args = _parser.parse_args()
SOURCE = _args.source_root.resolve()
sys.path.insert(0, str(SOURCE / "liber-primus/analysis/round13/B04"))
import harness as H  # noqa: E402
import ks  # noqa: E402
import skipdecode as sk  # noqa: E402

OUT = _args.output or pathlib.Path(__file__).with_name("b04-stage-microbench-20261023.json")
SEEDS = [("synthetic01", b"SYNTHETIC B04 SEED ONE"),
         ("synthetic02", b"SYNTHETIC B04 SEED TWO")]
TEXT = "THE PRIMES ARE SACRED AND THE PILGRIM SEEKS THE TRUTH "


def main():
    unit = sk.eng_to_idx(TEXT)
    plain = (unit * math.ceil(120 / len(unit)))[:120]
    known_key = ks.make_ks("sha256_ctr", "mod29", b"UNSEARCHED SYNTHETIC KEY", 512)
    cipher, _, _ = sk.encipher_keyskip(plain, known_key, sign=-1, supp=.83, seed=3301)
    seg = [H.make_segment("synthetic-head", cipher)]
    page_segs = [H.make_segment(f"synthetic-page-{i:02d}",
                                cipher[(i % 20):(i % 20) + 100])
                 for i in range(55)]
    rows = []
    for name, segs, reds, dirs, offs in [
        ("A", seg, None, ("fwd", "rev"), (0,)),
        ("B", seg, ["mod29", "rej29"], ("fwd", "rev"),
         (1, 4, 16, 29, 64, 128, 256, 512, 1024, 3301)),
        ("C", page_segs, ["mod29", "rej29"], ("fwd",), (0,)),
    ]:
        for nproc in (1, 2):
            r = H.run_stage(segs, SEEDS, reds=reds, dirs=dirs, offs=offs,
                            nproc=nproc, chunk_seeds=1, topk=5,
                            label=f"synthetic-{name}-{nproc}")
            rows.append({"stage": name, "processes": nproc,
                         "n_decodes": r["n_decodes"],
                         "elapsed_s": r["elapsed_s"],
                         "rate_per_s": r["n_decodes"] / r["elapsed_s"],
                         "best_score": r["rows"][0]["score"],
                         "top_rows_sha256": __import__("hashlib").sha256(
                             json.dumps(r["rows"], sort_keys=True).encode()).hexdigest()})
            print(name, nproc, rows[-1]["elapsed_s"], flush=True)
    OUT.write_text(json.dumps({"kind": "synthetic-only B04 source harness microbenchmark",
                               "source_commit": "f08b20b", "seed_hexes": [s.hex() for _, s in SEEDS],
                               "rows": rows}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT)


if __name__ == "__main__":
    main()
