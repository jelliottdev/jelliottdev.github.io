"""Execute pinned original key schedule, including the original call failure."""
import hashlib
import importlib
import json
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
from source_control import clock, groups, similarity

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--source-root", type=Path, required=True)
SOURCE = parser.parse_args().source_root.resolve()
PLAN = json.loads((HERE / "control-plan.json").read_text(encoding="utf-8"))
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == PLAN["source_revision"]
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    for name in ("LP/KeySearch.py", "LP/utils.py", "LP/RuneText.py", "LP/Rune.py", "LP/Alphabet.py"):
        data = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=SOURCE)
        if name in PLAN["source_blobs"]:
            assert hashlib.sha256(data).hexdigest() == PLAN["source_blobs"][name]
        (root / Path(name).name).write_bytes(data)
    sys.path.insert(0, str(root))
    K = importlib.import_module("KeySearch").GuessPattern
    samples = list(range(97))
    got_error = False
    try:
        K.groups(samples, 7, 2, 0)
    except TypeError:
        got_error = True
    assert got_error
    for k in range(3, 19):
        for s in range(1, k):
            for offset in range(k):
                source_clock = K.shift_pattern(k, s)
                for _ in range(offset):
                    next(source_clock)
                assert [next(source_clock) for _ in samples] == clock(k, s, offset, len(samples))
                assert K.groups(samples, k, K.shift_pattern(k, s), offset) == groups(samples, k, s, offset)
                assert K.zip(samples, list(range(k)), k, s, offset) == [
                    (n - col) % 29 for n, col in zip(samples, clock(k, s, offset, len(samples)))]
    test = [[(i * 5 + 3) % 29 for i in range(40)], [(i * 3 + 12) % 29 for i in range(40)]]
    model = [1 / 29] * 29
    orig_score, orig_key = K.guess(test, lambda arr: similarity(arr, model))
    independently = [min((similarity([(x - s) % 29 for x in part], model), s) for s in range(29)) for part in test]
    assert orig_key == [s for _, s in independently]
    assert abs(orig_score - sum(d for d, _ in independently) / len(test)) < 1e-15
    RuneText = importlib.import_module("RuneText").RuneText
    alphabet = importlib.import_module("Alphabet").RUNES
    for section in PLAN["source_sections"]:
        name = "pages/" + section + ".txt"
        raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=SOURCE)
        assert hashlib.sha256(raw).hexdigest() == PLAN["source_blobs"][name]
        decoded = raw.decode("utf-8")
        source_numbers = [x for x in RuneText(decoded).index_no_newline[:970] if x != 29]
        simple = [alphabet.index(c) for c in [ch for ch in decoded.strip() if ch not in "\r\n"][:970] if c in alphabet]
        assert source_numbers == simple, section
    print("PASS source TypeError, 1936 schedule/group/zip cases, guessed-column fixture, nine exact source parsings")
