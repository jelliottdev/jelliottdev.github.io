"""Test the source C1 search domain against its own planted feedback ciphers."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
LP = HERE / "source"
sys.path.insert(0, str(LP / "analysis" / "round12" / "C1"))
sys.path.insert(0, str(LP / "src"))
import control
import feedback as fb


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((HERE / "gate-plan.json").read_text(encoding="utf-8"))
    assert "[7,11,2]" in plan["plant"]
    P = control.eng_to_idx(control.PLAIN)
    assert len(P) == 212
    true_seed = [7, 11, 2]
    assert all([v, v, v] != true_seed for v in range(29))
    rows = []
    for mode in fb.SOURCES:
        for name, function in fb.F_BASIS.items():
            C = fb.encipher(P, function, 3, true_seed, source=mode, sign=-1)
            exact = fb.decode(C, function, 3, true_seed, source=mode, sign=-1)
            assert exact == P
            variants = ([([0, 0, 0], "0")] if mode == "ct" else
                        [([v, v, v], f"eq{v}") for v in range(29)])
            candidates = []
            for seed, label in variants:
                found = fb.decode(C, function, 3, seed, source=mode, sign=-1)
                sc = fb.score_norm(found[3:])
                recovery = sum(a == b for a, b in zip(found[3:], P[3:])) / (len(P)-3)
                candidates.append({"seed": label, "score": round(sc, 6),
                                   "recovery": round(recovery, 6)})
            best = max(candidates, key=lambda c: c["score"])
            rows.append({"mode": mode, "function": name, "true_seed_score": round(fb.score_norm(P[3:]), 6),
                         "best_searched_seed": best["seed"], "best_searched_score": best["score"],
                         "best_searched_recovery": best["recovery"],
                         "any_tried_seed_recovery_ge_90pct": any(c["recovery"] >= .9 for c in candidates),
                         "search_gate_pass": best["recovery"] >= .9 and best["score"] >= -5.5,
                         "all_seed_cases": candidates})
    summary = {mode: {"total": 7, "search_gate_pass": sum(r["search_gate_pass"] for r in rows if r["mode"] == mode),
                      "any_90pct": sum(r["any_tried_seed_recovery_ge_90pct"] for r in rows if r["mode"] == mode)}
               for mode in fb.SOURCES}
    output = {"schema": "liberpedia-r12-c1-source-domain-gate-v1",
              "gate_plan_sha256": digest(HERE / "gate-plan.json"),
              "source_control_plant": "k=3, sign=-1, true seed [7,11,2], 212-rune source English",
              "summary": summary, "rows": rows}
    with (HERE / "gate-results.json").open("w", encoding="utf-8", newline="\n") as file:
        json.dump(output, file, indent=2)
        file.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
