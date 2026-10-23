"""Exact bounded repaired-source grid; the original source itself fails before screening."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import random
import subprocess
from source_control import clock, groups, ioc, best_shifts

HERE = Path(__file__).resolve().parent
SOURCE = None
PLAN_BYTES = (HERE / "target-plan.json").read_bytes()
PLAN = json.loads(PLAN_BYTES)
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def blob(name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=SOURCE)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_blobs"][name], name
    return raw


def load():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == PLAN["source_revision"]
    counts = {r: int(n) for r, n in (line.split() for line in blob("data/p-1gram.txt").decode("utf8").splitlines())}
    probs = [counts.get(r, 0) / sum(counts.values()) for r in RUNES]
    rows = []
    for section in PLAN["source_sections"]:
        raw = blob("pages/" + section + ".txt").decode("utf8").strip()
        no_line_ends = [ch for ch in raw if ch not in "\r\n"][:970]
        nums = [RUNES.index(ch) for ch in no_line_ends if ch in RUNES]
        assert nums
        rows.append((section, nums, len(no_line_ends), len(raw)))
    return probs, rows


def scan(section, nums, expected, keep_outputs):
    report = []
    count_ioc = 0
    for k in range(3, 19):
        for step in range(1, k):
            for offset in range(k):
                parts = groups(nums, k, step, offset)
                score = sum(ioc(p) for p in parts) / k
                if not (1.6 < score < 2.1):
                    continue
                count_ioc += 1
                key, distance = best_shifts(parts, expected)
                if distance >= 0.1:
                    continue
                row = {"k": k, "step": step, "offset": offset, "ioc": score,
                       "similarity": distance, "key": key}
                if keep_outputs:
                    order = clock(k, step, offset, len(nums))
                    decoded = [(n - key[col]) % 29 for n, col in zip(nums, order)]
                    row["decoded_indices"] = decoded
                    row["decoded_sha256"] = hashlib.sha256(bytes(decoded)).hexdigest()
                report.append(row)
    return {"section": section, "runes": len(nums), "settings": 1936,
            "ioc_gate_count": count_ioc, "source_reports": report}


def null_job(arg):
    rep, section_number, section, nums, expected = arg
    trial = nums[:]
    random.Random(20261023 + 1000 * rep + section_number).shuffle(trial)
    result = scan(section, trial, expected, False)
    return rep, section_number, {
        "section": section,
        "ioc_gate_count": result["ioc_gate_count"],
        "source_report_count": len(result["source_reports"]),
        "best_similarity": min((x["similarity"] for x in result["source_reports"]), default=None),
    }


def main():
    global SOURCE
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("target", "null", "all"), default="all")
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    SOURCE = args.source_root.resolve()
    expected, rows = load()
    if args.mode in ("target", "all"):
        out = {"plan_sha256": hashlib.sha256(PLAN_BYTES).hexdigest(),
               "source_original_executable": False,
               "source_repair": PLAN["source_repair"],
               "sections": []}
        for section, nums, source_span, raw_count in rows:
            row = scan(section, nums, expected, True)
            row["source_prefix_symbols"] = source_span
            row["source_raw_symbols"] = raw_count
            out["sections"].append(row)
            print(section, "runes", len(nums), "IoC", row["ioc_gate_count"], "reported", len(row["source_reports"]), flush=True)
        if args.check:
            assert out == json.loads((HERE / "results.json").read_text(encoding="utf8"))
        else:
            (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    if args.mode in ("null", "all"):
        jobs = [(rep, n, section, nums, expected) for rep in range(49) for n, (section, nums, _, _) in enumerate(rows)]
        table = [[None] * len(rows) for _ in range(49)]
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            for done, (rep, n, summary) in enumerate(pool.map(null_job, jobs), 1):
                table[rep][n] = summary
                if done % 49 == 0:
                    print("null section jobs", done, "/", len(jobs), flush=True)
        summary = []
        for rep, section_rows in enumerate(table):
            assert all(section_rows)
            best = min((x["best_similarity"] for x in section_rows if x["best_similarity"] is not None), default=None)
            summary.append({"trial": rep, "sections": section_rows,
                            "source_report_count": sum(x["source_report_count"] for x in section_rows),
                            "global_best_similarity": best})
        out = {"plan_sha256": hashlib.sha256(PLAN_BYTES).hexdigest(), "null_trials": summary}
        if args.check:
            assert out == json.loads((HERE / "null-results.json").read_text(encoding="utf8"))
        else:
            (HERE / "null-results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
        print("null count", len(summary), "trials with report", sum(x["source_report_count"] > 0 for x in summary))


if __name__ == "__main__":
    main()
