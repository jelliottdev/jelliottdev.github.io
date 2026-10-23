"""Independent column arithmetic for every repaired source gate and 49 shared searches."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import random
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN_RAW = (HERE / "target-plan.json").read_bytes()
PLAN = json.loads(PLAN_RAW)
CONTROL = json.loads((HERE / "control-plan.json").read_text(encoding="utf8"))
RESULT = json.loads((HERE / "results.json").read_text(encoding="utf8"))
NULL = json.loads((HERE / "null-results.json").read_text(encoding="utf8"))
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
RUNE_ID = {r: i for i, r in enumerate(RUNES)}
SECTION_RANGES = [(0, 2), (3, 7), (8, 14), (15, 22), (23, 26), (27, 32), (33, 39), (40, 53), (54, 55)]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_bytes(root, name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=root)
    assert digest(raw) == PLAN["source_blobs"][name], name
    return raw


def exact_input(source_root):
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip() == PLAN["source_revision"]
    rows = []
    for (a, b), section in zip(SECTION_RANGES, PLAN["source_sections"]):
        assert section == f"p{a}-{b}"
        raw = source_bytes(source_root, "pages/" + section + ".txt").decode("utf8")
        whole = [RUNE_ID[ch] for ch in raw if ch in RUNE_ID]
        site = []
        for page in range(a, b + 1):
            path = ROOT / f"data/pages/lp2-{page:02}.json"
            data = json.loads(path.read_text(encoding="utf8"))
            site.extend(RUNE_ID[ch] for line in data["lines"] for ch in line["raw"] if ch in RUNE_ID)
        assert whole == site, section
        before = [ch for ch in raw.strip() if ch not in "\r\n"][:970]
        nums = [RUNE_ID[ch] for ch in before if ch in RUNE_ID]
        rows.append((section, nums))
    return rows


def max_column_ioc(nums):
    """Direct coordinate formula, independent of source iterator and run.py groups()."""
    maximum = 0.0
    passed = 0
    for k in range(3, 19):
        for step in range(1, k):
            for phase in range(k):
                counts = [[0] * 29 for _ in range(k)]
                sizes = [0] * k
                for position, symbol in enumerate(nums):
                    total = position + phase
                    column = ((total // k) * step + total % k) % k
                    counts[column][symbol] += 1
                    sizes[column] += 1
                total_ioc = 0.0
                for freq, size in zip(counts, sizes):
                    assert size >= 2
                    total_ioc += 29 * sum(c * (c - 1) for c in freq) / (size * (size - 1))
                avg = total_ioc / k
                maximum = max(maximum, avg)
                passed += 1.6 < avg < 2.1
    return maximum, passed


def null_job(arg):
    rep, number, section, nums = arg
    shuffled = nums[:]
    random.Random(20261023 + 1000 * rep + number).shuffle(shuffled)
    maximum, count = max_column_ioc(shuffled)
    return rep, number, section, maximum, count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    assert digest((HERE / "control-plan.json").read_bytes()) == PLAN["control_plan_sha256"]
    assert digest((HERE / "control-results.json").read_bytes()) == PLAN["control_output_sha256"]
    assert RESULT["plan_sha256"] == NULL["plan_sha256"] == digest(PLAN_RAW)
    rows = exact_input(args.source_root.resolve())
    assert len(rows) == len(RESULT["sections"]) == 9
    target = []
    for (section, nums), saved in zip(rows, RESULT["sections"]):
        maximum, passed = max_column_ioc(nums)
        assert saved["section"] == section and saved["runes"] == len(nums)
        assert saved["settings"] == 1936 and passed == saved["ioc_gate_count"] == 0
        assert saved["source_reports"] == []
        target.append({"section": section, "max_ioc": maximum, "ioc_gate_count": passed})
    jobs = [(rep, n, section, nums) for rep in range(49) for n, (section, nums) in enumerate(rows)]
    null_detail = [[None] * 9 for _ in range(49)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for rep, n, section, maximum, passed in pool.map(null_job, jobs):
            saved = NULL["null_trials"][rep]["sections"][n]
            assert saved["section"] == section and saved["ioc_gate_count"] == passed == 0
            assert saved["source_report_count"] == 0 and saved["best_similarity"] is None
            null_detail[rep][n] = maximum
    assert all(row["source_report_count"] == 0 and row["global_best_similarity"] is None for row in NULL["null_trials"])
    assert all(all(m is not None for m in trial) for trial in null_detail)
    report = {"schema": "liberpedia-relikd-pattern-independent-ioc-v1",
              "timing": "Post-result diagnostic; source gate and 49 shuffles were fixed earlier",
              "target": target,
              "target_max_ioc": max(x["max_ioc"] for x in target),
              "null_max_ioc": [max(trial) for trial in null_detail],
              "all_target_and_null_source_gate_counts_zero": True}
    dest = HERE / "ioc-diagnostic.json"
    if dest.exists():
        assert report == json.loads(dest.read_text(encoding="utf8"))
    else:
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("PASS 9 exact site/source streams, all 17,424 target cells and 49 whole-grid null trials")
    print("Largest target mean normalized 29×IoC:", round(report["target_max_ioc"], 4))


if __name__ == "__main__":
    main()
