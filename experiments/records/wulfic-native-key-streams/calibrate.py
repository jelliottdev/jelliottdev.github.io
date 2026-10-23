"""Supplemental power check for the pinned Stage I/M finite key streams.

This is our declared control, not part of the upstream Stage I/M outputs. It
uses the source's own anti-doublet encryptor and drift-tolerant score.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
SOURCE_HASHES = {
    "tools/run_stage_i.py": "7582b46f446338780ed4e3c4429bf3b70a2e1feed061d11ef4cc7f5a2fc962d6",
    "tools/run_stage_m.py": "eefb61156135a799039452e67a4973cd28b22952fcd2c643630fedbd70a5a7bb",
}
TRIALS = 20
SEED = 3301
LENGTHS = {
    "K-A primes": 729,
    "K-C word sums": 650,
    "K-D plaintext values": 729,
    "G-B bytes": 230,
    "G-5 5-bit groups": 368,
    "G-D base-60 digits": 460,
}


def render(source: Path) -> str:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if commit != COMMIT:
        raise ValueError(f"Wrong source revision: {commit}")
    for name, expected in SOURCE_HASHES.items():
        actual = hashlib.sha256((source / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Source file changed: {name} {actual}")
    sys.path.insert(0, str(source))
    corpus_mod = importlib.import_module("tools.lpcore.corpus")
    detect = importlib.import_module("tools.lpcore.detect")
    keys = importlib.import_module("tools.lpcore.keys")
    translation_mod = importlib.import_module("tools.lpcore.verify")
    stage_i = importlib.import_module("tools.run_stage_i")
    stage_m = importlib.import_module("tools.run_stage_m")
    corpus = corpus_mod.load_corpus()
    words = keys.solved_plaintext_words(corpus, translation_mod.load_translation())
    plain = [r for word in words for r in word]
    q = detect.unigram(plain)
    streams = stage_i.candidate_keys(words, 2 * 12956)
    streams.update(stage_m.grid_keys(corpus))
    assert set(streams) == set(LENGTHS)
    out = ["source\tkey_length\trunes\tseed\tpositive_log_lr\twrong_key_log_lr"]
    for name, length in LENGTHS.items():
        key = streams[name]
        assert length <= len(key) * .91
        for trial in range(TRIALS):
            seed = SEED + trial
            rng = random.Random(seed + sum(map(ord, name)))
            start = rng.randrange(len(plain))
            text = (plain[start:] + plain[:start]) * (length // len(plain) + 1)
            text = text[:length]
            cipher = keys.encrypt_dodging(text, key, keep=.19, seed=seed, rekey="next")
            wrong = keys.random_key(len(key), seed + 911)
            positive = detect.log_lr(cipher, key, q, mode="sub")
            negative = detect.log_lr(cipher, wrong, q, mode="sub")
            out.append(f"{name}\t{len(key)}\t{length}\t{seed}\t{positive:.2f}\t{negative:.2f}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = render(args.source_dir.resolve())
    target = HERE / "supplemental-controls.tsv"
    if args.check:
        assert target.read_text(encoding="utf-8") == data
        print("Stage I/M supplemental planted controls: OK")
    else:
        target.write_text(data, encoding="utf-8", newline="\n")
