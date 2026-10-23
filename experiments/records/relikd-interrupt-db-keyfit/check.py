"""Independent arithmetic check of each saved source candidate and plant."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def get(source, name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=source)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_sha256"][name]
    return raw.decode("utf8")


def runes(text):
    return [RUNES.index(c) for c in text if c in RUNES]


def fit(values, k, branch, target):
    key = []
    costs = []
    for residue in range(k):
        col = values[residue::k]
        candidates = []
        for a in ([1] if branch == "Vigenere" else range(29)):
            ainverse = pow(a, -1, 29) if a else 0
            for b in range(29):
                hist = [0] * 29
                for value in col:
                    decoded = ((value - b) * ainverse) % 29
                    hist[decoded] += 1
                loss = sum((hist[i] / len(col) - target[i]) ** 2 for i in range(29))
                candidates.append((loss, a, b))
        cost, a, b = min(candidates)
        costs.append(cost)
        key.append(b if branch == "Vigenere" else [a, b])
    return sum(costs) / k, key


def decrypt(values, branch, key, skips):
    result = []
    keypos = 0
    occurrence = 0
    for cipher in values:
        if cipher == 0:
            occurrence += 1
        if cipher == 0 and occurrence in skips:
            result.append(cipher)
            continue
        if branch == "Vigenere":
            plain = (cipher - key[keypos % len(key)]) % 29
        else:
            a, b = key[keypos % len(key)]
            plain = ((cipher - b) * (pow(a, -1, 29) if a else 0)) % 29
        result.append(plain)
        keypos += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == PLAN["source_revision"]
    saved = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    assert saved["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    grams = [line.split() for line in get(source, "data/p-1gram.txt").splitlines()]
    counts = {RUNES.index(glyph): int(count) for glyph, count in grams}
    total = sum(counts.values())
    target = [counts.get(i, 0) / total for i in range(29)]
    indices = {}
    for line in get(source, "db/db_indices.txt").splitlines():
        if line and not line.startswith("#"):
            section, amount, rune, locations = line.split("|")
            if int(rune) == 0:
                indices[section] = (int(amount), [int(x) for x in locations.split(",")] if locations else [])
    dbrows = []
    for n, line in enumerate(get(source, "db/db_norm.txt").splitlines(), 1):
        if line and not line.startswith("#"):
            section, count, score, rune, k, skips = line.split("|")
            if section in {"p0-2", "p27-32", "p40-53"} and float(score) >= 0.55 and int(rune) == 0:
                dbrows.append({"source_line": n, "section": section, "interrupt_count": int(count),
                               "saved_interrupt_score": float(score), "interrupt_index": int(rune),
                               "key_length": int(k),
                               "skip_occurrences": [int(v) for v in skips.split(",")] if skips else []})
    assert dbrows == PLAN["candidate_rows"]
    assert len(saved["target"]) == 18
    for row in dbrows:
        section = row["section"]
        whole = runes(get(source, f"pages/{section}.txt"))
        low, high = map(int, re.fullmatch(r"p(\d+)-(\d+)", section).groups())
        site = []
        for page_number in range(low, high + 1):
            page = json.loads((ROOT / "data" / "pages" / f"lp2-{page_number:02d}.json").read_text(encoding="utf8"))
            site.extend(runes(page["raw"]))
        assert site == whole, section
        amount, fpos = indices[section]
        assert len(whole) == amount
        assert fpos == [i for i, x in enumerate(whole) if x == 0]
        capped = fpos[20] if len(fpos) > 20 else amount
        cut = whole[:capped]
        for occurrence in reversed(row["skip_occurrences"]):
            cut.pop(fpos[occurrence - 1])
        for branch in ("Vigenere", "Affine"):
            match = next(x for x in saved["target"] if x["source_line"] == row["source_line"] and x["branch"] == branch)
            loss, key = fit(cut, row["key_length"], branch, target)
            restored = decrypt(whole, branch, key, row["skip_occurrences"])
            assert abs(loss - match["mean_similarity"]) < 1e-14
            assert key == match["key"]
            assert match["fit_prefix_runes"] == capped and match["fit_after_skips"] == len(cut)
            assert match["full_section_runes"] == len(whole)
            assert match["source_reported"] == (loss <= (0.05 if branch == "Vigenere" else 0.04))
            assert match["decoded_sha256"] == hashlib.sha256(bytes(restored)).hexdigest()
            assert match["decoded_prefix_indices"] == restored[:80]
    known = runes(get(source, "_solved.txt"))
    for control in saved["controls"]["matched_length"]:
        branch = control["branch"]
        length, k = control["runes"], control["key_length"]
        plain = known[:length]
        shifts = [(7*j+3)%29 for j in range(k)]
        multipliers = [((5*j+1)%28)+1 for j in range(k)]
        cipher = [((n+shifts[i%k]) if branch == "Vigenere" else (n*multipliers[i%k]+shifts[i%k]))%29 for i,n in enumerate(plain)]
        loss, key = fit(cipher, k, branch, target)
        restored = decrypt(cipher, branch, key, [])
        correct = shifts if branch == "Vigenere" else [[a,b] for a,b in zip(multipliers,shifts)]
        assert abs(loss-control["mean_similarity"])<1e-14
        assert control["key_slots_exact"] == sum(a==b for a,b in zip(key,correct))
        assert control["plaintext_runes_exact"] == sum(a==b for a,b in zip(restored,plain))
        assert control["full_key_exact"] == (key==correct)
        assert control["full_plaintext_exact"] == (restored==plain)
    for control in saved["controls"]["authentic"]:
        authentic = runes(get(source, "pages/p57_parable.txt"))
        score, key = fit(authentic, 1, control["branch"], target)
        assert control["exact"] == (decrypt(authentic, control["branch"], key, []) == authentic)
        assert key == control["key"] and abs(score-control["score"])<1e-14
    for control in saved["controls"]["skip_fixture"]:
        assert control["exact"] and control["source_output"] == control["manual_output"]
    print("PASS source/site section parity, nine exact source rows, 18 source-key fits/full decodes, six long plants and two authentic controls")


if __name__ == "__main__":
    main()
