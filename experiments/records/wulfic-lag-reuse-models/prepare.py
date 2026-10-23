"""Export source GP29 stream and solved-LP1 unigram model for independent checks."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from replay_source import PIN

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def site_stream():
    alphabet = {item["rune"]: item["index"] for item in json.loads(
        (ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    return bytes(alphabet[rune] for i in range(56)
                 for rune in json.loads((ROOT / f"data/pages/lp2-{i:02d}.json").read_text(encoding="utf-8"))["raw"]
                 if rune in alphabet)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source, text=True).strip() != PIN:
        raise AssertionError("Pinned source revision mismatch")
    sys.path.insert(0, str(args.source))
    from tools import run_stage_ac as ac
    from tools.lpcore.corpus import load_corpus
    corpus = load_corpus()
    source = bytes(ac.lp2_stream(corpus).tolist())
    if source != site_stream() or len(source) != 12956:
        raise AssertionError("Source/site GP29 streams differ")
    (HERE / "source-stream.bin").write_bytes(source)
    q = ac.plaintext_model(corpus).tolist()
    (HERE / "source-model.json").write_text(json.dumps({"source_commit": PIN, "q": q}, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    print("PASS: 12,956 source and site GP29 runes agree")


if __name__ == "__main__":
    main()
