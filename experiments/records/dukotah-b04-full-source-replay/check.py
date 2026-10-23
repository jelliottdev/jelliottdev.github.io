"""Offline byte and arithmetic checks for the packaged B04 replay."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check() -> dict:
    result = read(HERE / "results.json")
    assert result["source_revision"] == "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
    for rel, expected in result["source_file_sha256"].items():
        assert sha(HERE / "source/liber-primus" / rel) == expected, rel
    read_as_seed_text = {
        "cicada_koans_and_lp_sections.txt", "cicada_2012_2013_puzzle_texts.txt",
        "cicada_pgp_messages.txt"}
    for group, names in result["seed_filename_inputs"].items():
        directory = HERE / "source/liber-primus/data/keys" / group
        assert sorted(p.name for p in directory.iterdir() if p.is_file()) == names
        for name in names:
            if group != "armada18" or name not in read_as_seed_text:
                assert (directory / name).stat().st_size == 0, (group, name)
    summaries = {}
    for stage in "ABCD":
        p = HERE / f"replay/results_{stage}.json"
        assert sha(p) == result["result_file_sha256"][stage], stage
        summaries[stage] = read(p)
        assert summaries[stage]["complete"] is True, stage
        assert sha(HERE / f"replay/manifest_{stage}.json") == result["checkpoints"][stage]["manifest_file_sha256"]
        assert summaries[stage]["manifest_sha256"] == result["checkpoints"][stage]["manifest_sha256"]
        assert sha(p) == result["checkpoints"][stage]["merged_file_sha256"]
    assert sum(summaries[s]["n_decodes"] for s in "ABC") == 6_224_000
    assert [summaries[s]["n_decodes"] for s in "ABC"] == [1_385_600, 1_290_240, 3_548_160]
    for stage in "ABC":
        data = summaries[stage]
        assert data["n_decodes"] == data["expected_decodes"]
        assert sum(data["hist"]) == data["n_decodes"]
        assert data["source_stage_summary"]["hit"] is False
        assert data["source_stage_summary"]["over_bar"] == []
        assert data["source_stage_summary"]["bar"] == -5.5
        original = read(HERE / f"source/liber-primus/analysis/round13/B04/results_{stage}.json")
        for field in ("stage", "n_decodes", "best_score", "bar", "hit", "over_bar",
                      "hist", "hist_stats", "axis_best"):
            assert data["source_stage_summary"][field] == original[field], (stage, field)
        # Worker completion can reorder exactly tied rows, but all reported
        # top-50 case records still agree as a multiset at these stages.
        canonical = lambda rows: sorted(json.dumps(row, sort_keys=True, ensure_ascii=False)
                                        for row in rows)
        assert canonical(data["source_stage_summary"]["top50"]) == canonical(original["top50"])
    assert summaries["D"]["cells_saved"] == summaries["D"]["cells_expected"] == 300
    assert summaries["D"]["cells_reading_padded_zero"] == 0
    for row in summaries["D"]["source_stage_summaries"]:
        assert row["hit"] is False and row["over_bar"] == []
        assert row["n_improved_on_longer_text"] == 0
    archived_d = read(HERE / "source/liber-primus/analysis/round13/B04/results_D.json")
    for saved, archived in zip(summaries["D"]["source_stage_summaries"], archived_d):
        for field in ("stage", "n_decodes", "best_score", "bar", "hit", "over_bar",
                      "n_improved_on_longer_text"):
            assert saved[field] == archived[field], (saved["stage"], field)
    manifest = read(HERE / "replay/manifest_D.json")
    assert manifest["decoder_backend"]["name"] == "prefix_shared"
    assert len(manifest["ordered_picks"]) == 150
    assert len(manifest["segments"]) == 2
    for segment in range(2):
        for index in range(150):
            cell = read(HERE / f"replay/D-cells/cell-{segment:02d}-{index:03d}.json")
            body = cell["payload"]
            canonical = json.dumps(body, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":")).encode("utf-8")
            assert hashlib.sha256(canonical).hexdigest() == cell["payload_sha256"]
            assert body["manifest_sha256"] == summaries["D"]["manifest_sha256"]
            assert body["segment_index"] == segment and body["pick_index"] == index
            assert not body["key_access_audit"]["source_zero_padding_read"]
    gate = read(HERE / "replay/G2-check.json")
    assert gate["G2_pass"] is True and gate["plant_rank"] == 1
    assert gate["candidate_decodes"] == summaries["A"]["n_decodes"]
    g1 = read(HERE / "replay/G1-preflight.json")
    bound_gate = read(HERE / "replay/G2-gate.json")
    assert g1["g1_current_code_pass"] and g1["full_message"]["full_message_gate_pass"]
    assert sha(HERE / "replay/G1-preflight.json") == bound_gate["g1_preflight_sha256"]
    assert bound_gate["G1_pass"] and bound_gate["G2_pass"]
    for path, expected in g1["source_files"].items():
        assert sha(HERE / "source" / path) == expected, path
    seed_module = HERE / "source/liber-primus/analysis/round13/B04/seeds.py"
    spec = importlib.util.spec_from_file_location("b04_bundled_seeds", seed_module)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seeds = [{"label": name, "seed_hex": payload.hex()} for name, payload in module.build()]
    packed = json.dumps(seeds, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":")).encode("utf-8")
    assert len(seeds) == 2165
    assert hashlib.sha256(packed).hexdigest() == gate["ordered_seed_manifest_sha256"]
    direct = read(HERE / "replay/direct-original-validation.json")
    assert direct["all_returned_fields_equal"] and direct["all_key_access_fields_equal"]
    assert direct["all_frozen_book_raw_fields_equal"] and direct["all_frozen_book_raw_key_reads_equal"]
    assert direct["page0_cells"] == 150 and direct["preselected_book_indices"] == [0, 49, 99, 149]
    assert result["stage_best"]["D"] == {r["stage"]: r["best_score"] for r in summaries["D"]["source_stage_summaries"]}
    return {"source_files": len(result["source_file_sha256"]), "head_decodes": 6_224_000,
            "follow_up_cells": 300, "direct_source_cells": direct["source_decoder_cells"],
            "G2_rank": gate["plant_rank"], "pass": True}


if __name__ == "__main__":
    print(json.dumps(check(), sort_keys=True))
