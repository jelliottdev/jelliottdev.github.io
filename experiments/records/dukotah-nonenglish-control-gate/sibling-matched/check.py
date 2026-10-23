"""Audit the pinned C1 matched-runic control rule from its saved rows.

This checks source evidence and arithmetic; it does not rerun plants or LP2 decodes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ELIGIBLE = ("LATIN", "GREEK", "EN_NOVOWEL")


def canonical(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def audit() -> dict:
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    for item in plan["inputs"]:
        path = HERE / item["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item["sha256"], f"source changed: {item['path']}"

    prereg = (HERE / "source-PREREG.md").read_text(encoding="utf-8")
    control = (HERE / "source-control.py").read_text(encoding="utf-8")
    assert "Power = fraction of\nreplicates whose adjudicated score exceeds the register's OWN seed-3301 order-matched null bar" in prereg
    assert "matched power > English power on >=1 non-English register at L=120" in prereg
    assert '"matched_beats_english": (mq_power > en_power) or (mq_power_fixed > en_power_fixed)' in control
    assert 'if v["L"] == 120 and v["panel"] in ("LATIN", "GREEK", "EN_NOVOWEL")' in control

    saved = json.loads((HERE / "source-out_control.json").read_text(encoding="utf-8"))
    rows = []
    for name in ELIGIBLE:
        key = f"{name}|120"
        row = saved["summary"][key]
        assert row["n"] == 24 and row["L"] == 120 and row["panel"] == name
        own_null = row["power_MATCHED"] > row["power_EN"]
        fixed_minus_5_5 = row["power_MATCHED_fixed_bar_L7A"] > row["power_EN_fixed_bar_L7A"]
        executed = own_null or fixed_minus_5_5
        assert executed == row["matched_beats_english"], key
        rows.append({
            "register": name,
            "plants": row["n"],
            "own_null_english": row["power_EN"],
            "own_null_matched": row["power_MATCHED"],
            "fixed_bar_english": row["power_EN_fixed_bar_L7A"],
            "fixed_bar_matched": row["power_MATCHED_fixed_bar_L7A"],
            "frozen_rule_pass": own_null,
            "executed_rule_pass": executed,
        })
    frozen = any(r["frozen_rule_pass"] for r in rows)
    executed = any(r["executed_rule_pass"] for r in rows)
    assert saved["control_pass"] == executed
    assert saved["control_pass_registers"] == [f"{r['register']}|120" for r in rows if r["executed_rule_pass"]]
    source_result = json.loads((HERE / "source-results.json").read_text(encoding="utf-8"))
    assert source_result["n_decodes"] == plan["source_reported_manuscript_grid"]
    return {
        "schema": "liberpedia-source-control-sibling-audit-results-v1",
        "source_revision": plan["revision"],
        "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "source_reported_manuscript_grid": plan["source_reported_manuscript_grid"],
        "locally_rerun_manuscript_grid": False,
        "eligible_registers": rows,
        "frozen_rule_pass": frozen,
        "executed_rule_pass": executed,
        "source_saved_control_pass": saved["control_pass"],
        "finding": "0 of 3 eligible registers beat English under each scorer's own null; the executed OR passes Latin using an unrelated fixed −5.5 bar.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = canonical(audit())
    output = HERE / "results.json"
    if args.check:
        assert output.read_bytes() == data, "saved result changed"
        print("C1 matched control sibling: checked")
    else:
        output.write_bytes(data)
        print("C1 matched control sibling: wrote results")


if __name__ == "__main__":
    main()
