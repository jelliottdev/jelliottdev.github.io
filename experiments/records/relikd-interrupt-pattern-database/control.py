"""Pre-target known-text detection gate for the saved pattern databases."""

import hashlib
import ast
import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
SOURCE = Path(__file__).resolve().parents[4] / "source-cache" / "relikd-text"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def blob(name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=SOURCE)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_sha256"][name]
    return raw


def original_classes(target):
    """Load only two exact pinned source classes, without redistributing them."""
    ns = {"TARGET_IOC": target, "normalized_probability": lambda a: [x / sum(a) for x in a]}
    for path, name in (("LP/KeySearch.py", "GuessPattern"), ("LP/Probability.py", "Probability")):
        raw = blob(path).decode("utf8")
        tree = ast.parse(raw)
        klass = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == name)
        exec(compile(ast.Module(body=[klass], type_ignores=[]), path, "exec"), ns)
    return ns["GuessPattern"], ns["Probability"]


def mirror(k, variant, n):
    pattern = list(range(k)) + (list(range(k - 1, -1, -1)) if variant == "a" else list(range(k - 2, 0, -1)))
    return [pattern[i % len(pattern)] for i in range(n)]


def score(values, k, kind, target):
    groups = [values[i::k] for i in range(k)]
    ics = []
    for group in groups:
        hist = Counter(group)
        n = len(group)
        ics.append(29 * sum(v * (v - 1) for v in hist.values()) / (n * (n - 1)))
    if kind == "high":
        return sum(ics) / k
    return 1 - sum(abs(x - target) for x in ics) / k


def score_mirror(values, k, variant, kind, target):
    groups = [[] for _ in range(k)]
    for x, g in zip(values, mirror(k, variant, len(values))):
        groups[g].append(x)
    ics = []
    for group in groups:
        hist = Counter(group)
        n = len(group)
        ics.append(29 * sum(v * (v - 1) for v in hist.values()) / (n * (n - 1)))
    if kind == "high":
        return sum(ics) / k
    return 1 - sum(abs(x - target) for x in ics) / k


def scores(values, kind, target, mirror_type=None):
    f = (lambda k: score_mirror(values, k, mirror_type, kind, target)) if mirror_type else (lambda k: score(values, k, kind, target))
    return {str(k): f(k) for k in range(2, 9)}


def run():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip() == PLAN["source_revision"]
    known = [RUNES.index(c) for c in blob("_solved.txt").decode("utf8") if c in RUNES][:600]
    assert len(known) == 600
    counts = [0] * 29
    for line in blob("data/p-1gram.txt").decode("utf8").splitlines():
        rune, count = line.split()
        counts[RUNES.index(rune)] = int(count)
    total = sum(counts)
    target = 29 * sum(n * (n - 1) for n in counts) / (total * (total - 1))
    SourcePattern, SourceProbability = original_classes(target)
    out = {"known_runes": len(known), "known_sha256": hashlib.sha256(bytes(known)).hexdigest(), "source_target_ioc": target, "rows": []}
    # The source's two mirror schedules give distinct position-to-key maps.
    for variant in ("a", "b"):
        clock = mirror(5, variant, len(known))
        cipher = [(x + ((7 * clock[i] + 3) % 29)) % 29 for i, x in enumerate(known)]
        recovered = [(x - ((7 * clock[i] + 3) % 29)) % 29 for i, x in enumerate(cipher)]
        assert recovered == known
        for kind in ("high", "norm"):
            s = scores(cipher, kind, target, variant)
            for k in range(2, 9):
                generator = SourcePattern.mirror_pattern_a(k) if variant == "a" else SourcePattern.mirror_pattern_b(k)
                groups = SourcePattern.groups(cipher, k, generator)
                ref = SourceProbability.parts_high(groups, k) if kind == "high" else SourceProbability.parts_norm(groups, k)
                assert abs(s[str(k)] - ref) < 1e-12, (variant, kind, k)
            out["rows"].append({"family": "mirror", "variant": variant, "kind": kind, "scores": s,
                                "true_period_strict_winner": s["5"] > max(v for k, v in s.items() if k != "5"),
                                "full_known_recovery": True})

    # For modulo-a, F insertions are removed before the modulo split. For
    # modulo-b, raw positions are split first and F insertions removed within
    # each subgroup; both rules recover the original 600 known runes.
    inserted = set(range(37, 625, 37))
    for family in ("modulo_a", "modulo_b"):
        for modulus in (2, 3):
            for mo in range(modulus):
                raw = []
                plain_by_raw = []
                key_by_raw = []
                joined_group_counts = [0] * modulus
                raw_group_counts = [0] * modulus
                pointer = 0
                position = 0
                while pointer < len(known):
                    if position in inserted:
                        raw.append(0)
                        plain_by_raw.append(None)
                        key_by_raw.append(None)
                        position += 1
                        continue
                    group = (pointer % modulus) if family == "modulo_a" else (position % modulus)
                    clock = joined_group_counts[group] if family == "modulo_a" else raw_group_counts[group]
                    key = (7 * ((clock + group) % 5) + 3) % 29
                    raw.append((known[pointer] + key) % 29)
                    plain_by_raw.append(known[pointer])
                    key_by_raw.append(key)
                    joined_group_counts[group] += 1
                    raw_group_counts[group] += 1
                    pointer += 1
                    position += 1
                assert [x for x in plain_by_raw if x is not None] == known
                assert [(x - key) % 29 for x, key in zip(raw, key_by_raw) if key is not None] == known
                if family == "modulo_a":
                    joined = [x for i, x in enumerate(raw) if i not in inserted]
                    subsection = joined[mo::modulus]
                else:
                    subsection = [x for i, x in enumerate(raw) if i % modulus == mo and i not in inserted]
                for kind in ("high", "norm"):
                    s = scores(subsection, kind, target)
                    for k in range(2, 9):
                        ref = SourceProbability.IC_w_keylen(subsection, k) if kind == "high" else SourceProbability.target_diff(subsection, k)
                        assert abs(s[str(k)] - ref) < 1e-12, (family, modulus, mo, kind, k)
                    out["rows"].append({"family": family, "modulus": modulus, "subgroup": mo, "kind": kind,
                                        "raw_runes": len(raw), "inserted_f": len(inserted.intersection(range(len(raw)))),
                                        "subgroup_runes": len(subsection), "scores": s,
                                        "true_period_strict_winner": s["5"] > max(v for k, v in s.items() if k != "5"),
                                        "full_known_recovery": True})
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    SOURCE = args.source_root.resolve()
    out = run()
    path = HERE / "control-results.json"
    if args.check:
        assert json.loads(path.read_text(encoding="utf8")) == out
    else:
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print(len(out["rows"]), "controls", sum(r["true_period_strict_winner"] for r in out["rows"]), "strict winners")
