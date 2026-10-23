"""Independent source-class replay of every saved mirror/modulo score."""

import argparse
import ast
import bisect
import hashlib
import itertools
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN_BYTES = (HERE / "plan.json").read_bytes()
PLAN = json.loads(PLAN_BYTES)
RESULT = json.loads((HERE / "results.json").read_text(encoding="utf8"))
CONTROL = json.loads((HERE / "control-results.json").read_text(encoding="utf8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def check(source):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() == PLAN["source_revision"]

    def blob(name):
        raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=source)
        assert hashlib.sha256(raw).hexdigest() == PLAN["source_sha256"][name]
        return raw

    counts = [0] * 29
    for line in blob("data/p-1gram.txt").decode("utf8").splitlines():
        rune, number = line.split()
        counts[RUNES.index(rune)] = int(number)
    n = sum(counts)
    target = 29 * sum(x * (x - 1) for x in counts) / (n * (n - 1))
    assert abs(RESULT["source_target_ioc"] - target) < 1e-15
    ns = {"TARGET_IOC": target, "itertools": itertools, "bisect": bisect,
          "normalized_probability": lambda a: [x / sum(a) for x in a]}
    for path, name in (("LP/KeySearch.py", "GuessPattern"), ("LP/Probability.py", "Probability"),
                       ("LP/InterruptSearch.py", "InterruptSearch")):
        raw = blob(path).decode("utf8")
        node = next(x for x in ast.parse(raw).body if isinstance(x, ast.ClassDef) and x.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), ns)
    Pattern, Probability, InterruptSearch = ns["GuessPattern"], ns["Probability"], ns["InterruptSearch"]

    indices = {}
    for line in blob("db/db_indices.txt").decode("utf8").splitlines():
        if line.startswith("#") or not line:
            continue
        name, total, irp, positions = line.split("|")
        indices.setdefault(name, {"total": int(total), "runes": {}})["runes"][int(irp)] = [int(x) for x in positions.split(",") if x]
    sections = {}
    for name in indices:
        path = "pages/" + name + ".txt"
        if path in PLAN["source_sha256"]:
            sections[name] = [RUNES.index(x) for x in blob(path).decode("utf8") if x in RUNES]
            assert len(sections[name]) == indices[name]["total"]

    expected = []
    for family, filenames in PLAN["families"].items():
        for filename in filenames:
            kind = "high" if "db_high_" in filename else "norm"
            if family == "mirror":
                m = re.search(r"_mirror_([ab])\.(\d+)\.txt$", filename)
                assert m and int(m[2]) == 0
                variant = m[1]
            else:
                m = re.search(r"_mod_[ab]_([23])\.([0-2])\.txt$", filename)
                assert m
                modulus, subgroup = int(m[1]), int(m[2])
            for lineno, line in enumerate(blob(filename).decode("utf8").splitlines(), 1):
                if line.startswith("#") or not line:
                    continue
                name, interrupt_count, printed, irp, keylen, skips = line.split("|")
                irp, keylen = int(irp), int(keylen)
                full = sections[name]
                positions = indices[name]["runes"][irp]
                if family == "modulo_b":
                    all_stops = [(p - subgroup) // modulus for p in positions if p % modulus == subgroup]
                    limit = (all_stops[20] if len(all_stops) > 20 else len(full[subgroup::modulus]))
                    data = full[subgroup::modulus][:limit]
                else:
                    all_stops = positions
                    limit = all_stops[20] if len(all_stops) > 20 else len(full)
                    data = full[:limit]
                stop = all_stops[:20]
                assert int(interrupt_count) == len(stop)
                skips = [int(x) for x in skips.split(",") if x]
                removed = [stop[i - 1] for i in skips]
                joined = InterruptSearch(data, irp=irp, irp_stops=stop).join(removed)
                if family == "modulo_a":
                    joined = joined[subgroup::modulus]
                if family == "mirror":
                    gen = Pattern.mirror_pattern_a(keylen) if variant == "a" else Pattern.mirror_pattern_b(keylen)
                    parts = Pattern.groups(joined, keylen, gen, 0)
                    value = Probability.parts_high(parts, keylen) if kind == "high" else Probability.parts_norm(parts, keylen)
                else:
                    value = Probability.IC_w_keylen(joined, keylen) if kind == "high" else Probability.target_diff(joined, keylen)
                assert abs(value - float(printed)) <= 5.01e-6, (filename, lineno, value, printed)
                expected.append((filename, lineno, name, irp, keylen, skips, len(data), len(joined), value))

    assert RESULT["plan_sha256"] == hashlib.sha256(PLAN_BYTES).hexdigest()
    assert len(expected) == RESULT["row_count"] == len(RESULT["rows"]) == 7407
    for checkrow, row in zip(expected, RESULT["rows"]):
        filename, lineno, name, irp, keylen, skips, prefix, after, value = checkrow
        assert (row["file"], row["line"], row["section"], row["interrupt_index"], row["key_length"], row["skip_occurrences"], row["fit_prefix_runes"], row["after_skip_runes"]) == (filename, lineno, name, irp, keylen, skips, prefix, after)
        assert abs(row["recounted_score"] - value) < 1e-12
    known = [RUNES.index(c) for c in blob("_solved.txt").decode("utf8") if c in RUNES][:600]
    assert len(known) == CONTROL["known_runes"] == 600
    assert hashlib.sha256(bytes(known)).hexdigest() == CONTROL["known_sha256"]
    assert abs(target - CONTROL["source_target_ioc"]) < 1e-15
    for receipt in CONTROL["rows"]:
        if receipt["family"] == "mirror":
            variant = receipt["variant"]
            gen = Pattern.mirror_pattern_a(5) if variant == "a" else Pattern.mirror_pattern_b(5)
            clock = list(itertools.islice(gen, len(known)))
            ciphertext = [(plain + ((7 * clock[i] + 3) % 29)) % 29 for i, plain in enumerate(known)]
            assert [(value - ((7 * clock[i] + 3) % 29)) % 29 for i, value in enumerate(ciphertext)] == known

            def source_score(k):
                generator = Pattern.mirror_pattern_a(k) if variant == "a" else Pattern.mirror_pattern_b(k)
                parts = Pattern.groups(ciphertext, k, generator)
                return Probability.parts_high(parts, k) if receipt["kind"] == "high" else Probability.parts_norm(parts, k)
        else:
            modulus, subgroup = receipt["modulus"], receipt["subgroup"]
            raw = []
            keys = []
            count = [0] * modulus
            pointer = 0
            while pointer < len(known):
                position = len(raw)
                if position in range(37, 625, 37):
                    raw.append(0)
                    keys.append(None)
                    continue
                group = pointer % modulus if receipt["family"] == "modulo_a" else position % modulus
                key = (7 * ((count[group] + group) % 5) + 3) % 29
                raw.append((known[pointer] + key) % 29)
                keys.append(key)
                count[group] += 1
                pointer += 1
            assert [(rune - key) % 29 for rune, key in zip(raw, keys) if key is not None] == known
            skip = set(range(37, 625, 37))
            selected = ([x for i, x in enumerate(raw) if i not in skip][subgroup::modulus]
                        if receipt["family"] == "modulo_a"
                        else [x for i, x in enumerate(raw) if i % modulus == subgroup and i not in skip])
            assert len(raw) == receipt["raw_runes"] and len(selected) == receipt["subgroup_runes"]

            def source_score(k):
                return Probability.IC_w_keylen(selected, k) if receipt["kind"] == "high" else Probability.target_diff(selected, k)

        for k in range(2, 9):
            assert abs(source_score(k) - receipt["scores"][str(k)]) < 1e-12, (receipt, k)
    assert len(CONTROL["rows"]) == 24
    assert sum(x["true_period_strict_winner"] for x in CONTROL["rows"]) == 22
    assert all(x["full_known_recovery"] for x in CONTROL["rows"])
    assert all((x["scores"]["5"] > max(v for k, v in x["scores"].items() if k != "5")) == x["true_period_strict_winner"] for x in CONTROL["rows"])
    print("PASS exact source-class score parity for 7,407 saved rows, 24 frozen control receipts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    check(args.source_root.resolve())
