"""Write the three-entry T3 batch receipt from completed fresh outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = HERE.relative_to(ROOT).as_posix()


def evidence(*names):
    out = []
    for name in names:
        path = HERE / "evidence" / name
        assert path.is_file(), path
        out.append({"path": f"{PREFIX}/evidence/{name}",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return out


def command(script, output):
    return {"command": f"python {script}", "exit_code": 0,
            "output_path": f"{PREFIX}/evidence/{output}"}


receipt = {
    "schema": "liberpedia-source-batch-worker-receipt-v1",
    "worker": "worker-c",
    "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
    "frozen_plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
    "note": "Fresh pinned-source T3 perturbation and LP1 decoder outputs. Conditional rune changes are not verified manuscript corrections. T1's reader uses global canon-derived labels, so its checks are transductive rather than independent held-out truth.",
    "entries": [
        {"source_id": "T3-PROPAGATION-MAP", "state": "partial",
         "evidence": evidence("t3-input-manifest.json", "input-snapshot.json", "out_baseline.json", "out_random.json", "out_targeted.json", "t3_baseline.fresh.log", "t3_sensitivity.fresh.log", "t3_targeted.fresh.log"),
         "executions": [command("t3_baseline.py", "out_baseline.json"), command("t3_sensitivity.py", "out_random.json"), command("t3_targeted.py", "out_targeted.json")],
         "covered_subclaim": "Fresh source-run baseline and exact 400-trial random, dense and targeted perturbation statistics on the pinned 12,956-rune stream; planted flip, 13 baseline values and 450-position gate passed. Source numeric outputs match its archived rows within floating-order tolerance.",
         "remaining": ["The 62-ledger-entry dependency_map.json remains the pinned source's static classification; its entire historical script tree was not rehydrated and t3_depmap.py was not freshly rerun.", "Perturbing source transcription is not image adjudication or a proof of canon correctness."]},
        {"source_id": "T3-OAE450-STREAM-POSITIONS", "state": "replayed",
         "evidence": evidence("input-snapshot.json", "out_baseline.json", "out_targeted.json", "t3_targeted.fresh.log"),
         "executions": [command("t3_baseline.py", "out_baseline.json"), command("t3_targeted.py", "out_targeted.json")],
         "covered_subclaim": "All 450 source O/A/AE disagreements mapped to distinct canonical stream coordinates; changing each to its source alternative changes exact adjacent doublets 86 to 103 and normalized IoC 0.999874 to 1.013823.",
         "remaining": ["A mapped machine disagreement is not a confirmed transcription error; source T1 training reuses global canon-derived labels."]},
        {"source_id": "T3-S2-DECODE-FRAGILITY", "state": "partial",
         "evidence": evidence("t3-input-manifest.json", "t1-input-manifest.json", "out_decode_L120_LP1.json", "out_decode_L400_LP1.json", "t3_decode_L120.fresh.log", "t3_decode_L400.fresh.log"),
         "executions": [command("t3_decode.py 120 120 LP1", "out_decode_L120_LP1.json"), command("t3_decode.py 400 60 LP1", "out_decode_L400_LP1.json")],
         "covered_subclaim": "Fresh full 14-level source grid for each of LP1 L120 (120 replicates) and L400 (60 replicates), with F0 beam parity gate; correct-key recovery falls below 90% at source k_book=1800 and 900 respectively. Both outputs reproduce pinned source endpoints.",
         "remaining": ["The full-book L12956 KJV register needs data/kjv.txt, absent from the pinned source revision; no alternate corpus was substituted.", "Fixtures test a known key and English-register scoring, not recovery of an LP2 key or all cipher models."]},
    ],
}
(HERE / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("wrote", HERE / "receipt.json")
