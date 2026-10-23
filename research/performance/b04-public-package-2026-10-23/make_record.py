"""Package the independently checked B04 source replay without rerunning 6.2M cells."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import runpy

REPO = pathlib.Path(__file__).resolve().parents[3]
HERE = REPO / "experiments/records/dukotah-b04-full-source-replay"
WORK = REPO.parent
UPSTREAM = WORK / "source-cache/dukotah-cicada3301"
SOURCE = UPSTREAM / "liber-primus"
PERF = REPO / "research/performance"
PIN = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"

SOURCE_FILES = (
    "analysis/round13/B04/harness.py", "analysis/round13/B04/sweep.py",
    "analysis/round13/B04/ks.py", "analysis/round13/B04/seeds.py",
    "analysis/round13/B04/control.py", "analysis/campaign18_skip/skipdecode.py",
    "analysis/round11/lib_numchannel.py", "src/lp/score.py",
    "data/english_quadgrams.txt", "data/krisyotam_runes.txt",
    "analysis/run_stats.py", "src/lp/gematria.py",
    "src/lp/ciphers.py", "src/lp/stats.py", "src/lp/corpus.py",
    "data/keys/thematic.txt", "data/keys/armada18/cicada_koans_and_lp_sections.txt",
    "data/keys/armada18/cicada_2012_2013_puzzle_texts.txt",
    "data/keys/armada18/cicada_pgp_messages.txt",
    "analysis/pp49_51/canon_256.bin", "analysis/pp49_51/canon_256_decpref.bin",
    "data/keys/self_reliance.txt",
    "analysis/round13/B04/PREREG.md", "analysis/round13/B04/GATE-NOTE.md",
    "analysis/round13/B04/RESULTS.md", "analysis/round13/B04/results_gates.json",
    "analysis/round13/B04/results_G1_rerun.json",
    "analysis/round13/B04/results_A.json", "analysis/round13/B04/results_B.json",
    "analysis/round13/B04/results_C.json", "analysis/round13/B04/results_D.json",
)


def copy(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: pathlib.Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def main() -> None:
    for rel in SOURCE_FILES:
        copy(SOURCE / rel, HERE / "source/liber-primus" / rel)
    # seeds.py reads the names (not contents) of these two directories as
    # additional seed tokens. Preserve all names without shipping ~100 MB of
    # unrelated book text; the three files whose content is read are above.
    filename_inputs = {}
    for group in ("armada18", "armada19"):
        upstream_dir = SOURCE / "data/keys" / group
        target_dir = HERE / "source/liber-primus/data/keys" / group
        names = sorted(p.name for p in upstream_dir.iterdir() if p.is_file())
        filename_inputs[group] = names
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            target = target_dir / name
            if not target.exists():
                target.write_bytes(b"")
    copy(UPSTREAM / "LICENSE", HERE / "source/LICENSE")
    copy(PERF / "b04-2026-10-23/resumable.py", HERE / "replay/b04-2026-10-23/resumable.py")
    # The archived wrapper's provenance gate requires a Git checkout at the
    # upstream commit. The downloadable bundle has exact bytes but no .git;
    # replace only that source-loading gate with the declared byte hashes.
    portable = HERE / "replay/b04-2026-10-23/resumable.py"
    code = portable.read_text(encoding="utf-8")
    start = code.index("def load_source(source):")
    end = code.index("\ndef stage_inputs(", start)
    code = code[:start] + '''def load_source(source):
    expected = json.loads((pathlib.Path(__file__).resolve().parents[2] / "results.json")
                          .read_text(encoding="utf-8"))
    if expected["source_revision"] != PIN:
        raise ValueError("bundle source revision mismatch")
    root = source / "liber-primus"
    hashes = {p: sha(root / p) for p in SOURCE_FILES}
    for path, actual in hashes.items():
        if expected["source_file_sha256"].get(path) != actual:
            raise ValueError(f"bundled source differs from pinned bytes: {path}")
    b04 = root / "analysis/round13/B04"
    sys.path.insert(0, str(b04))
    import harness as H
    import seeds as S
    import ks
    import skipdecode as sk
    return H, S, ks, sk, hashes

''' + code[end:]
    portable.write_text(code, encoding="utf-8", newline="\n")
    copy(PERF / "b04-stage-b-2026-10-23/resumable_d.py", HERE / "replay/b04-stage-b-2026-10-23/resumable_d.py")
    copy(PERF / "beam-prefix-sharing-2026-10-23/beam_shared.py",
         HERE / "replay/beam-prefix-sharing-2026-10-23/beam_shared.py")
    for stage in "ABCD":
        copy(WORK / f"b04-lp2-{stage}-20261023/merged.json", HERE / f"replay/results_{stage}.json")
        copy(WORK / f"b04-lp2-{stage}-20261023/manifest.json", HERE / f"replay/manifest_{stage}.json")
        copy(PERF / f"b04-stage-{stage.lower()}-2026-10-23/independent-check.json",
             HERE / f"replay/check_{stage}.json")
    for p in sorted((WORK / "b04-lp2-D-20261023").glob("cell-*.json")):
        copy(p, HERE / "replay/D-cells" / p.name)
    copy(PERF / "b04-stage-d-2026-10-23/direct-original-validation.json",
         HERE / "replay/direct-original-validation.json")
    copy(PERF / "b04-stage-c-2026-10-23/stage-d-frozen-candidates.json",
         HERE / "replay/stage-d-frozen-candidates.json")
    copy(PERF / "b04-g2-2026-10-23/independent-check.json", HERE / "replay/G2-check.json")
    copy(PERF / "b04-g2-2026-10-23/gate-receipt.json", HERE / "replay/G2-gate.json")
    copy(REPO / "research/control-preflights/b04-2026-10-23.json", HERE / "replay/G1-preflight.json")
    checks = {stage: json.loads((HERE / f"replay/check_{stage}.json").read_text(encoding="utf-8"))
              for stage in "ABCD"}
    summaries = {stage: json.loads((HERE / f"replay/results_{stage}.json").read_text(encoding="utf-8"))
                 for stage in "ABCD"}
    result = {
        "schema": "b04-full-source-replay-v1", "source_revision": PIN,
        "g2": json.loads((HERE / "replay/G2-check.json").read_text(encoding="utf-8")),
        "stage_counts": {stage: summaries[stage].get("n_decodes", summaries[stage].get("cells_saved"))
                         for stage in "ABCD"},
        "head_total": sum(summaries[s]["n_decodes"] for s in "ABC"),
        "stage_best": {stage: (summaries[stage]["source_stage_summary"]["best_score"] if stage != "D"
                               else {item["stage"]: item["best_score"]
                                     for item in summaries["D"]["source_stage_summaries"]})
                       for stage in "ABCD"},
        "source_bar": -5.5,
        "checkpoints": {stage: checks[stage] for stage in "ABCD"},
        "raw_original_validation": {
            "all_returned_fields_equal": True, "all_key_access_fields_equal": True,
            "book_indices": [0, 49, 99, 149], "source_decoder_cells": 154},
        "result_file_sha256": {stage: sha(HERE / f"replay/results_{stage}.json") for stage in "ABCD"},
        "source_file_sha256": {rel: sha(HERE / "source/liber-primus" / rel) for rel in SOURCE_FILES},
        "seed_filename_inputs": filename_inputs,
        "note": "A/B/C are source-worker results. D uses a source-equivalent accelerated representation checked against 154 unchanged-source decoder cells.",
    }
    write_json(HERE / "results.json", result)
    runpy.run_path(str(HERE / "plot.py"))
    prefix = "experiments/records/dukotah-b04-full-source-replay/"
    input_files = [HERE / name for name in ("plan.json", "run.py", "check.py", "plot.py")]
    input_files += [p for p in (HERE / "source").rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts
                    and p.suffix not in (".pyc", ".pyo")]
    input_files += [p for p in (HERE / "replay").rglob("*.py")]
    output_files = [HERE / "results.json", HERE / "scores.svg"]
    output_files += [p for p in (HERE / "replay").rglob("*.json") if p.is_file()]
    def declare(paths):
        return [{"path": prefix + p.relative_to(HERE).as_posix(), "sha256": sha(p)}
                for p in sorted(paths)]
    record = {
        "id": "dukotah-b04-full-source-replay", "status": "draft",
        "title": "Cryptographic seed streams across the unsolved pages",
        "question": "Does the pinned B04 dictionary and skip-aware decoder find a source-scored English reading in the unsolved manuscript?",
        "reader_question": "Can a short Cicada-related seed generate the manuscript's key?",
        "summary": "Full pinned B04 A/B/C search plus D follow-up, with planted-message gate and original-decoder crosschecks.",
        "finding": "The planted message ranked first, but none of 6,224,000 manuscript opening decodes or 300 selected whole-page/book decodes cleared the source's −5.5 score bar. The highest manuscript score was −5.885 on short page starts.",
        "limitations": "Only this seed dictionary, generators, reductions, offsets, skip model and English scorer were tested. The planted control covers a 120-rune opening, not every full-book reading. Reversed keys may change prefix when source key length changes between short and long runs; tied scores can change cutoff order.",
        "next_steps": "Any extension should name new seed bytes or key construction and first show that its decoder recovers a planted message of comparable length under the same selection procedure.",
        "outcome": "not-supported",
        "tags": ["B-04", "source replay", "derived key", "cryptographic keystream", "seed dictionary", "skip-aware decoder"],
        "pages_note": "LP2-00–55; the pinned transcription has no runes for LP2-50, so source stage C has 55 nonempty segments.",
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56) if i != 50],
            "artifacts": [prefix + "source/liber-primus/data/krisyotam_runes.txt"],
            "representation": "Pinned GP29 rune indices in source reading order. A/B use first 120 joined unsolved runes; C uses up to 100 runes at each of 55 source page starts; D uses the 262-rune first page and 12,956-rune joined stream.",
            "procedure": "Run G1/G2 source controls, full A/B/C seed-generator grids with English quadgram scorer and soft key-skip beam, then replay the source-selected 150 settings on both long targets. Independent checker validates saved merge, hashes and direct source-decoder comparisons.",
            "parameters": "2,165 A seeds, 504 B/C core seeds, 16 generators, source reduction/sign/Atbash/direction/offset axes, beam width 400, max three skips per rune, fixed score bar −5.5; 6,224,000 opening decodes and 300 D cells.",
            "exclusions": "Other seeds, salts, key stretching, generators, boundary resets, text layers, languages, scoring rules and skip models; full held-out detector-power calibration."
        },
        "review": {"reviewer": "Exact source replay with independent checkpoint, archive and raw decoder checks",
                   "retested_on": "2026-10-23", "kind": "computational source replay", "human_review": "pending"},
        "reproduction": {
            "command": "python experiments/records/dukotah-b04-full-source-replay/run.py --check",
            "environment": "Python 3.12; cryptography is needed for the complete 16-generator grid. --quick works offline in seconds; --full uses four workers by default, writes external checkpoints and takes many minutes.",
            "script": prefix + "run.py", "script_sha256": sha(HERE / "run.py"),
            "inputs": declare(input_files), "outputs": declare(output_files),
        },
        "visuals": [{"path": prefix + "scores.svg", "caption": "The planted full-grid control clears the source bar; the best LP2 results from each stage do not."}],
        "sources": [{"label": "Pinned B04 plan", "url": f"https://github.com/Dukotah/cicada3301/blob/{PIN}/liber-primus/analysis/round13/B04/PREREG.md"},
                    {"label": "Pinned B04 executable", "url": f"https://github.com/Dukotah/cicada3301/blob/{PIN}/liber-primus/analysis/round13/B04/harness.py"},
                    {"label": "Pinned B04 source results", "url": f"https://github.com/Dukotah/cicada3301/blob/{PIN}/liber-primus/analysis/round13/B04/RESULTS.md"}],
        "related": ["b04-source-seeds-opening-cribs", "public-kdf-seed-stretch"],
    }
    write_json(HERE / "record.json", record)
    print(json.dumps({"head_total": result["head_total"], "stage_best": result["stage_best"]}))


if __name__ == "__main__":
    main()
