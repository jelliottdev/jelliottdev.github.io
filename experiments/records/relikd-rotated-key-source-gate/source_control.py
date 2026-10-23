"""Control-only gate for a minimal, explicitly repaired source pattern schedule."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = None
PLAN = json.loads((HERE / "control-plan.json").read_text(encoding="utf-8"))


def blob(name):
    raw = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=SOURCE)
    assert hashlib.sha256(raw).hexdigest() == PLAN["source_blobs"][name]
    return raw


def clock(k, step, offset, n):
    seq = []
    i = 0
    while len(seq) < n + offset:
        start = i * step % k
        seq.extend(range(start, k))
        seq.extend(range(start))
        i += 1
    return seq[offset:offset + n]


def groups(nums, k, step, offset):
    result = [[] for _ in range(k)]
    for col, value in zip(clock(k, step, offset, len(nums)), nums):
        result[col].append(value)
    return result


def ioc(nums):
    counts = [0] * 29
    for n in nums:
        counts[n] += 1
    l = len(nums)
    return 29 * sum(c * (c - 1) for c in counts) / (l * (l - 1))


def similarity(nums, expected):
    counts = [0] * 29
    for n in nums:
        counts[n] += 1
    return sum((c / len(nums) - t) ** 2 for c, t in zip(counts, expected))


def best_shifts(parts, expected):
    out = []
    distances = []
    for part in parts:
        opts = [(similarity([(x - shift) % 29 for x in part], expected), shift) for shift in range(29)]
        distance, shift = min(opts)
        out.append(shift)
        distances.append(distance)
    return out, sum(distances) / len(distances)


def main():
    global SOURCE
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    SOURCE = args.source_root.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == PLAN["source_revision"]
    for name in PLAN["source_blobs"]:
        blob(name)
    readings_raw = (ROOT / PLAN["known_readings"]["path"]).read_bytes()
    assert hashlib.sha256(readings_raw).hexdigest() == PLAN["known_readings"]["sha256"]
    controls = json.loads(readings_raw)["controls"]
    plain = [x for c in controls for p in c["decoded_pages"] for x in p["rune_indices"]][:970]
    assert len(plain) == 970
    freq = {r: int(n) for r, n in (line.split() for line in blob("data/p-1gram.txt").decode("utf-8").splitlines())}
    runes = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
    count = [freq.get(r, 0) for r in runes]
    model = [x / sum(count) for x in count]
    planted = PLAN["control"]["plant_generator"]
    key = PLAN["control"]["plant_key"]
    seq = clock(planted["length"], planted["step"], planted["offset"], len(plain))
    cipher = [(p + key[j]) % 29 for p, j in zip(plain, seq)]
    true_parts = groups(cipher, 7, 2, 0)
    true_ioc = sum(ioc(p) for p in true_parts) / 7
    inferred, true_dist = best_shifts(true_parts, model)
    decoded = [(c - inferred[j]) % 29 for c, j in zip(cipher, seq)]
    assert decoded == plain if inferred == key else True
    in_ioc = 1.6 < true_ioc < 2.1
    in_dist = true_dist < 0.1
    gated = []
    for k in range(3, 19):
        for step in range(1, k):
            for offset in range(k):
                parts = groups(cipher, k, step, offset)
                average_ioc = sum(ioc(p) for p in parts) / k
                if 1.6 < average_ioc < 2.1:
                    candidate_key, distance = best_shifts(parts, model)
                    if distance < 0.1:
                        order = clock(k, step, offset, len(cipher))
                        recovered = sum((c - candidate_key[col]) % 29 == p for c, col, p in zip(cipher, order, plain))
                        gated.append({"k": k, "step": step, "offset": offset, "similarity": distance, "exact": recovered})
    result = {"source_bug": "TypeError on first groups(..., integer step, ...) call", "known_runes": len(plain), "true_model": {"k":7,"step":2,"offset":0,"ioc":true_ioc,"similarity":true_dist,"inferred_key":inferred,"planted_key":key,"exact_runes":sum(a==b for a,b in zip(decoded,plain)),"ioc_gate":in_ioc,"similarity_gate":in_dist}, "whole_grid":{"cases":1936,"source_report_count":len(gated),"best_similarity":min(gated,key=lambda q:q['similarity']) if gated else None,"exact_recovery_models":sum(q['exact']==970 for q in gated),"contains_true_model":any((q['k'],q['step'],q['offset'])==(7,2,0) for q in gated)}}
    if args.check:
        assert result == json.loads((HERE / "control-results.json").read_text(encoding="utf8"))
    else:
        (HERE / "control-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n")
    print("PASS known-reading control: 970 exact runes; sole source report among 1,936 settings")


if __name__ == "__main__":
    main()
