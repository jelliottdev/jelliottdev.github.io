"""Independent exact-row and planted recovery audit, without producer imports."""
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
RUNE_STRING = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
PRIME = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109]


def source_bytes(source, name):
    data = subprocess.check_output(["git", "show", PLAN["source_revision"] + ":" + name], cwd=source)
    assert hashlib.sha256(data).hexdigest() == PLAN["source_sha256"][name]
    return data


def feedback(values, seed, is_prime, plus):
    state = seed
    output = bytearray()
    for value in values:
        step = PRIME[state] if is_prime else state
        state = (value + (step if plus else -step)) % 29
        output.append(state)
    return bytes(output)


def score(values):
    n = len(values)
    counts = Counter(values)
    return 29 * sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))


def check(source):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() == PLAN["source_revision"]
    saved = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    assert saved["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    sections = {s: [RUNE_STRING.index(c) for c in source_bytes(source, "pages/" + s + ".txt").decode("utf8") if c in RUNE_STRING]
                for s in PLAN["sections"]}
    positions = {}
    for line in source_bytes(source, "db/db_indices.txt").decode("utf8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, total, rune, listed = line.split("|")
        positions[(name, int(rune))] = [int(x) for x in listed.split(",") if x]
        if name in sections:
            assert len(sections[name]) == int(total)
    actual = []
    for filename in PLAN["files"]:
        token = Path(filename).stem.split("autokey_")[1]
        plus = token[0] == "+"
        is_prime = token[1] == "p"
        inverse = token.endswith("_inv")
        for lineno, text in enumerate(source_bytes(source, filename).decode("utf8").splitlines(), 1):
            if not text.strip() or text.startswith("#"):
                continue
            section, count_text, score_text, irp, seed_text, chosen_text = text.split("|")
            assert irp == "0"
            stops = positions[(section, 28 if inverse else 0)][:16]
            assert len(stops) == int(count_text)
            full_stops = positions[(section, 28 if inverse else 0)]
            end = full_stops[16] if len(full_stops) > 16 else len(sections[section])
            selected = [int(x) for x in chosen_text.split(",") if x]
            assert selected == sorted(set(selected))
            omit = {stops[x - 1] for x in selected}
            assert len(omit) == len(selected)
            path = [sections[section][i] for i in range(end) if i not in omit]
            if inverse:
                path = [28 - x for x in path]
            plain = feedback(path, int(seed_text) or 1, is_prime, plus)
            value = score(plain)
            assert abs(value - float(score_text)) <= 5.00001e-6, (filename, lineno, value, score_text)
            actual.append((filename, lineno, section, len(plain), hashlib.sha256(plain).hexdigest(), value))
    rows = saved["rows"]
    assert len(rows) == len(actual) == saved["row_count"]
    for row, checked in zip(rows, actual):
        assert (row["file"], row["line"], row["section"], row["scored_runes"], row["decoded_sha256"]) == checked[:5]
        assert abs(row["recounted_score"] - checked[5]) < 1e-12

    controls = json.loads((HERE / "control-results.json").read_text(encoding="utf8"))
    known = bytes(RUNE_STRING.index(c) for c in source_bytes(source, "_solved.txt").decode("utf8") if c in RUNE_STRING)[:96]
    assert len(known) == 96
    assert len(controls["rows"]) == 8
    for row in controls["rows"]:
        token = Path(row["file"]).stem.split("autokey_")[1]
        plus = token[0] == "+"
        is_prime = token[1] == "p"
        state = 7
        encrypted = []
        for p in known:
            step = PRIME[state] if is_prime else state
            encrypted.append((p - (step if plus else -step)) % 29)
            state = p
        raw = encrypted[:]
        for at in PLAN["known_control"]["injected_interrupt_raw_positions"]:
            raw.insert(at, 0)
        if token.endswith("_inv"):
            raw = [28 - x for x in raw]
        skips = set(PLAN["known_control"]["injected_interrupt_raw_positions"])
        accepted = [x for i, x in enumerate(raw) if i not in skips]
        if token.endswith("_inv"):
            accepted = [28 - x for x in accepted]
        decoded = feedback(accepted, 7, is_prime, plus)
        assert decoded == known
        assert row["recovered_indices_sha256"] == hashlib.sha256(decoded).hexdigest()
        assert abs(row["true_primer_score"] - score(decoded)) < 1e-12
        ranks = [score(feedback(accepted, seed, is_prime, plus)) for seed in range(29)]
        assert row["fixed_skip_primer_rank"] == 1 + sum(x > score(decoded) for x in ranks)
    print("PASS", len(actual), "saved rows,", len(controls["rows"]), "complete known-text controls")


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("--source-root", type=Path, required=True)
    args = arg.parse_args()
    check(args.source_root.resolve())
