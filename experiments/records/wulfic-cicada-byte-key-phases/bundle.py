"""Convert the independently pinned Stage R source profile into safe NumPy data.

The replay's temporary pickle is an internal intermediate only. The public
bundle contains numeric arrays and JSON labels, and never loads pickled data.
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    with args.profile.open("rb") as handle:
        profile = pickle.load(handle)  # Own trusted replay output; not user input.
    names = list(profile["keys"])
    segments = list(profile["ciphers"])
    labels = json.dumps({"names": names, "segments": segments,
                         "by_cost": profile["by_cost"]}, ensure_ascii=False,
                        separators=(",", ":")).encode("utf-8")
    arrays = {
        "labels": np.frombuffer(labels, dtype=np.uint8),
        "ratio": np.asarray(profile["ratio"], dtype=np.float64),
        "plain": np.asarray(profile["plain"], dtype=np.uint8),
    }
    arrays.update({f"key_{i}": np.asarray(profile["keys"][name], dtype=np.uint8)
                   for i, name in enumerate(names)})
    arrays.update({f"segment_{i}": np.asarray(profile["ciphers"][name], dtype=np.uint8)
                   for i, name in enumerate(segments)})
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.destination, **arrays)
    print(args.destination, args.destination.stat().st_size)


if __name__ == "__main__":
    main()
