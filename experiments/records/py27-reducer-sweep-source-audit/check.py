"""Independent receipt and source-path checks; does not import the audit runner."""
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
LANE = BASE / "source/liber-primus/analysis/round21/L3-py27-reducers-plus-64bit-map"


def main() -> None:
    result = json.loads((BASE / "results.json").read_text(encoding="utf-8"))
    source = json.loads((LANE / "out_reducers.json").read_text(encoding="utf-8"))
    positive = json.loads((LANE / "out_poscontrol.json").read_text(encoding="utf-8"))
    lines = (LANE / "reducers_sweep.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines[1:]]
    assert json.loads(lines[0]) == source["header"]
    assert len(rows) == 95 == result["verified_saved_survivor_rows"]
    assert source["total_words_screened"] == sum(c["words_screened"] for c in source["per_config"])
    assert source["total_words_screened"] == 884000
    assert positive["PASS_all"] and len(positive["configs"]) == 4
    assert all(c["PASS"] for c in positive["configs"])
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["config"]].append(row)
        assert not row["hit"] and not row["clears"] and row["pmax"] < source["header"]["claim_bar_pmax"]
    assert sum(len(v) for v in grouped.values()) == 95
    for c in source["per_config"]:
        rr = grouped[c["config"]]
        assert len(rr) == c["survivors_stage_b"]
        assert max(x["pmax"] for x in rr) == c["top_survivors_by_pmax"][0]["pmax"]
    assert max(x["pmax"] for x in rows) == result["verified_saved_max_stage_b_pmax"] == 6.248

    # Reconstruct the 45,975-word priority front without using run.py or sweep.py.
    source_prior = BASE / "source/liber-primus/analysis/round20/P3/seedprior20.json"
    order = json.loads(source_prior.read_text(encoding="utf-8"))["order"]
    words = dict.fromkeys(int(x["seed"]) & 0xFFFFFFFF for x in order)
    for x in order[:64]:
        for offset in range(-512, 513):
            words[(int(x["seed"]) + offset) & 0xFFFFFFFF] = None
    assert len(words) == 45975 == result["unique_prior_front_words"]
    digest = hashlib.sha256("".join(f"{w}\n" for w in words).encode()).hexdigest()
    assert digest == result["prior_front_sha256"]

    # Inspect the two independent source call sites. The planted control calls
    # full H.evaluate directly; it never invokes the 120-rune stage_a function.
    pc = ast.parse((LANE / "poscontrol.py").read_text(encoding="utf-8"))
    sw = ast.parse((LANE / "sweep.py").read_text(encoding="utf-8"))
    pc_fun = next(n for n in pc.body if isinstance(n, ast.FunctionDef) and n.name == "run_config")
    worker = next(n for n in sw.body if isinstance(n, ast.FunctionDef) and n.name == "worker")
    calls = lambda node: [x.func.id if isinstance(x.func, ast.Name) else x.func.attr
                          for x in ast.walk(node) if isinstance(x, ast.Call)
                          and isinstance(x.func, (ast.Name, ast.Attribute))]
    assert "evaluate" in calls(pc_fun) and "stage_a" not in calls(pc_fun)
    assert "stage_a" in calls(worker)
    assert result["gate_audit"]["stage_a_recall_on_plants_verified"] is False

    missing = result["absent_required_source_inputs"]
    assert len(missing) == 4 and all(not (BASE / "source" / name).exists() for name in missing)
    print("PASS: source receipt arithmetic, 95 persisted rows, priority front, and Stage-A control gap")


if __name__ == "__main__":
    main()
