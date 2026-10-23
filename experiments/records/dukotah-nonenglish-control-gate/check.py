"""Re-evaluate R24-C1-ext's frozen control gate from pinned source receipts.

This does not rerun the manuscript decoder or independently rebuild the corpora.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ("LATIN", "GREEK", "OLD_ENGLISH", "ENOCHIAN")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    manifest = json.loads((HERE / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["revision"] == "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
    for name, expected in manifest["sha256"].items():
        path = HERE / ("LICENSE.source" if name == "LICENSE" else "source-" + name)
        assert sha(path) == expected, f"Pinned source changed: {name}"

    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    assert tuple(plan["registers"]) == NAMES
    prereg = (HERE / "source-PREREG.md").read_text(encoding="utf-8")
    control_py = (HERE / "source-control.py").read_text(encoding="utf-8")
    assert re.search(r"Control PASS for a register iff its language-LM\s+power > the English quadgram power", prereg)
    assert "passed = lm_d > en_d" in control_py
    assert 'if v["panel"] in noneng and v["lm_beats_english"]' in control_py
    saved = json.loads((HERE / "source-out_control.json").read_text(encoding="utf-8"))
    reported = json.loads((HERE / "source-results.json").read_text(encoding="utf-8"))
    assert saved["nrep"] == 24 and saved["nnull"] == 60
    assert reported["n_decodes"] == 20480

    rows = []
    for name in NAMES:
        row = saved["summary"][f"{name}|120"]
        en = row["power_EN"]
        lm = row["power_LM"]
        d_en = row["dprime_EN"]
        d_lm = row["dprime_LM"]
        frozen_pass = lm > en
        executed_pass = d_lm > d_en
        assert row["n"] == 24
        assert row["lm_beats_english"] == executed_pass
        rows.append({
            "register": name,
            "n_plants": row["n"],
            "english_power": en,
            "own_model_power": lm,
            "english_dprime": d_en,
            "own_model_dprime": d_lm,
            "frozen_gate_pass": frozen_pass,
            "executed_gate_pass": executed_pass,
        })
    frozen_validated = [r["register"] for r in rows if r["frozen_gate_pass"]]
    executed_validated = [r["register"] for r in rows if r["executed_gate_pass"]]
    assert sorted(saved["validated_registers"]) == sorted(executed_validated)
    assert sorted(reported["validated_registers"]) == sorted(executed_validated)
    return {
        "plan_sha256": sha(HERE / "plan.json"),
        "source_revision": manifest["revision"],
        "source_lane": plan["source_lane"],
        "audit_basis": "Pinned source plan, code and saved 24-plant/60-null control summaries; not a rerun of their raw simulations or manuscript grid.",
        "rows": rows,
        "frozen_validated_registers": frozen_validated,
        "executed_validated_registers": executed_validated,
        "frozen_nonenglish_control_pass": bool(frozen_validated),
        "executed_nonenglish_control_pass": saved["control_pass"],
        "reported_manuscript_decodes_not_locally_rerun": reported["n_decodes"],
        "reported_manuscript_survivors": reported["survivors"],
        "conclusion": "No non-English register meets the frozen strict power-advantage rule. The source used a different d-prime gate to continue. Its reported zero survivors is not a control-validated exclusion under the preregistered rule.",
    }


if __name__ == "__main__":
    result = audit()
    target = HERE / "results.json"
    expected = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if target.exists():
        assert target.read_text(encoding="utf-8") == expected, "Audit result differs"
        print("PASS: pinned control-gate audit matches results.json")
    else:
        target.write_text(expected, encoding="utf-8", newline="\n")
        print("Wrote", target)
