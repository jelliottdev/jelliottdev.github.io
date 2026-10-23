"""Pre-outcome source-parity and planted-recovery gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

import numpy as np

from core import decode, one_ioc, parse, source_name_to_effective

HERE = pathlib.Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    args = ap.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    data = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest() == plan["inputs_sha256"]
    source = subprocess.check_output(["git", "-C", str(args.source_root), "show", "HEAD:" + plan["source"]["path"]])
    assert hashlib.sha256(source).hexdigest() == plan["source"]["sha256"]
    env = {"__name__": "source_module"}
    exec(compile(source, "pinned source", "exec"), env)

    source_page = next(p for p in data["pages"] if p["source_ordinal"] == 28)
    text = source_page["text"]
    source_cipher, _ = env["extract_runes"](text)
    cipher, prior = parse(text, data["source_literal_runes"], data["separators"])
    assert source_cipher == cipher.tolist()
    parity = 0
    for direction in ("clockwise", "counterclockwise"):
        for letter, separator in ((0, 0), (7, 5), (28, 1), (13, 17)):
            for mode in ("sub", "add", "beaufort"):
                direct = env["alberti_decrypt"](text, direction == "clockwise", letter, separator, mode)
                effective = source_name_to_effective(direction, letter, separator, mode)
                ours = decode(cipher, prior, *effective)
                assert direct == ours.tolist()
                parity += 1

    plants = []
    for parser, alphabet in (("literal", data["source_literal_runes"]), ("canonical", data["canonical_runes"])):
        _, layout = parse(text, alphabet, data["separators"])
        layout = layout[:250]
        assert len(layout) == 250
        for reading in data["readings"]:
            plain = np.asarray(reading["first_250"], dtype=np.int16)
            position = np.arange(250, dtype=np.int16)
            artificial_cipher = (plain + 7 * position + 5 * layout) % 29
            recovered = decode(artificial_cipher, layout, 1, -7 % 29, -5 % 29)
            assert np.array_equal(recovered, plain)
            measure = one_ioc(recovered)
            assert measure > 1.4
            plants.append({"parser": parser, "reading": reading["id"], "ioc": measure, "exact": True})

    result = {
        "schema": "wulfic-separator-clock-gate-v1",
        "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
        "source_parity_cases": parity,
        "plants": plants,
        "passed": parity == 24 and len(plants) == 8,
    }
    (HERE / "gate_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("source parity", parity, "planted recoveries", len(plants), "PASS")


if __name__ == "__main__":
    main()
