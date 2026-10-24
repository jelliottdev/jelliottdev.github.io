"""Check reviewed row-reversal comparison metadata against saved evidence.

Reads and hashes existing files only. Does not run the route search, English
scorer, controls or model. --self-test also rejects in-memory corruptions.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

BASELINE = "lp2-row-column-routes"
ENGLISH = "lp2-row-column-english"
OPERATION = {"action": "reverse", "operand": "rune-order", "within": "row"}
SETTING = ("row", False, True, False)
INPUT = "The test kept headings and row order, and removed spaces and other non-rune symbols."
PROSE = {
    BASELINE: {
        "description": "The first 12 output runes were compared with nine fixed known openings.",
        "limitation": "Other beginnings and general English readability are not decided by this test.",
        "reuse": "Complete output indices and source-position traces are saved.",
    },
    ENGLISH: {
        "description": "The full output was scored using frequencies of four-letter groups in English.",
        "limitation": "LP2-49 and LP2-55 are score-ineligible; LP2-50 is empty. Scores do not establish readability.",
        "reuse": "Saved scores can be checked against the corresponding full outputs.",
    },
}


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def read(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(case):
    return tuple(case[name] for name in ("axis", "outer_reverse", "inner_reverse", "alternating"))


def verify_hashes(root, record):
    reproduction = record["reproduction"]
    count = 0
    for role in ("inputs", "outputs"):
        for entry in reproduction[role]:
            relative = Path(entry["path"])
            path = (root / relative).resolve()
            need(not relative.is_absolute() and path.is_relative_to(root), "Dependency escapes root")
            need(digest(path) == entry["sha256"], "Declared dependency hash mismatch: " + entry["path"])
            count += 1
    need(digest(root / reproduction["script"]) == reproduction["script_sha256"], "Producer script hash mismatch")
    return count + 1


def verify_page(page, raw, alphabet, openings):
    need(hashlib.sha256(raw).hexdigest() == page["source_sha256"], "Saved source-page hash mismatch")
    lookup = {entry["rune"]: entry["index"] for entry in alphabet}
    positions, rows = [], []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        runes = [lookup[char] for char in line if char in lookup]
        row = []
        for column, index in enumerate(runes, 1):
            ordinal = len(positions)
            row.append(ordinal)
            positions.append({"ordinal": ordinal, "line": line_number, "rune_position": column, "index": index})
        if row:
            rows.append(row)
    need(positions == page["source_positions"], "Source coordinates/indices differ: " + page["page"])
    cases = page["cases"]
    need(len(cases) == (16 if positions else 0), "Wrong route count: " + page["page"])
    need(len({key(case) for case in cases}) == len(cases), "Duplicate route settings")
    for case in cases:
        order = case["source_ordinals"]
        need(sorted(order) == list(range(len(positions))), "Saved route is not a complete permutation")
        need(case["output_indices"] == [positions[n]["index"] for n in order], "Output differs from saved source trace")
        matches = [opening["id"] for opening in openings if case["output_indices"][:12] == opening["indices"]]
        need(matches == case["matching_openings"], "Opening matches differ")
    if not positions:
        return None
    selected = [case for case in cases if key(case) == SETTING]
    need(len(selected) == 1, "Missing/duplicate exact row-reversal setting")
    expected = [ordinal for row in rows for ordinal in reversed(row)]
    need(selected[0]["source_ordinals"] == expected, "Exact setting does not reverse each source row")
    return selected[0]


def verify_english(report, route_pages, alphabet):
    rows = report["observed_cases"]
    need(len(rows) == report["parameter_routes"] == 880, "English route count differs")
    lookup = {(page["page"], key(case)): case for page in route_pages for case in page["cases"]}
    seen, scored_pages, unscored_pages = set(), [], []
    for row in rows:
        identity = (row["page"], key(row))
        need(identity not in seen and identity in lookup, "Missing/duplicate English route join")
        seen.add(identity)
        output = lookup[identity]["output_indices"]
        groups = max(0, sum(len(alphabet[index]["latin"]) for index in output) - 3)
        need(row["runes"] == len(output) and row["quadgrams"] == groups, "English input extent differs")
        eligible = groups >= 100
        need((row["score"] is not None) == eligible, "Score eligibility differs from fixed 100-group rule")
        if eligible:
            need(isinstance(row["score"], (int, float)) and math.isfinite(row["score"]), "Invalid saved score")
        if key(row) == SETTING:
            (scored_pages if eligible else unscored_pages).append(row["page"])
    need(seen == set(lookup), "English ledger does not join every generated route")
    need(sum(row["score"] is not None for row in rows) == report["eligible_routes"] == 848, "Eligible count differs")
    need(unscored_pages == ["lp2-49", "lp2-55"], "Unexpected score-ineligible pages")
    return scored_pages


def expected_metadata(identifier, pages):
    prose = PROSE[identifier]
    return {
        "version": 1,
        "operation": OPERATION,
        "executed_pages": pages,
        "evaluation": {
            "kind": "known-opening" if identifier == BASELINE else "english-score",
            "description": prose["description"],
            "limitation": prose["limitation"],
        },
        "input_description": INPUT,
        "reuse": prose["reuse"],
    }


def rejects(action, label):
    try:
        action()
    except (AssertionError, KeyError, ValueError, TypeError):
        return
    raise AssertionError("Self-test accepted " + label)


def schema_tests(root, records):
    """Exercise publication schema and checker export without building files."""
    path = Path(__file__).with_name("build_experiments.py")
    specification = importlib.util.spec_from_file_location("row_metadata_schema", path)
    builder = importlib.util.module_from_spec(specification)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        specification.loader.exec_module(builder)
    finally:
        sys.dont_write_bytecode = previous
    pages = {page["id"] for page in read(root, "data/index.json")["pages"]}
    for name, record in records.items():
        actual = builder.validate_record(root, root / f"experiments/records/{name}/record.json", pages)
        need(actual["recorded_comparison"] == record["recorded_comparison"], "Publication validation changed metadata")
    valid = records[BASELINE]["recorded_comparison"]
    scope = records[BASELINE]["scope"]
    validate = lambda value: builder.validate_recorded_comparison(value, scope, pages)
    invalid = []
    for key, value in (("version", True), ("version", 2), ("extra", "unreviewed"),
                       ("executed_pages", []), ("executed_pages", ["lp2-15", "lp2-15"]),
                       ("executed_pages", ["lp2-17", "lp2-15"]), ("executed_pages", ["lp2-56"]),
                       ("executed_pages", ["LP2-15"]), ("executed_pages", ["lp2-58"])):
        bad = copy.deepcopy(valid)
        bad[key] = value
        invalid.append(bad)
    for field, value in (("operation", {"action": "reverse", "operand": "word-order", "within": "row"}),
                         ("evaluation", {"kind": "readability", "description": "Test", "limitation": "Unknown"})):
        bad = copy.deepcopy(valid)
        bad[field] = value
        invalid.append(bad)
    for text in ("", " leading", "trailing ", "\ufeffLeading BOM", "line\nbreak", "[source]", "`code`", "*bold*", "back\\slash", "delete\x7f", "x" * 501, "\U0001f600" * 251):
        bad = copy.deepcopy(valid)
        bad["reuse"] = text
        invalid.append(bad)
    for bad in invalid:
        rejects(lambda bad=bad: validate(bad), "invalid recorded comparison schema")
    for text in ("x" * 500, "\U0001f600" * 250, "\x85Not ECMAScript trim whitespace\x85", "a < b & c > d"):
        boundary = copy.deepcopy(valid)
        boundary["reuse"] = text
        validate(boundary)
    # JSON 1.0 and JavaScript number 1 are the same schema version.
    boundary = copy.deepcopy(valid)
    boundary["version"] = 1.0
    validate(boundary)
    exported = builder.checker_payload(list(records.values()), b"test registry")
    need(all(row["recorded_comparison"] == records[row["id"]]["recorded_comparison"]
             for row in exported["records"]), "Compact checker omits or changes reviewed metadata")
    return len(invalid) + 5 + len(records) + 1


def check(root, self_test=False):
    records = {name: read(root, f"experiments/records/{name}/record.json") for name in (BASELINE, ENGLISH)}
    hashes = sum(verify_hashes(root, record) for record in records.values())
    route_plan = read(root, f"experiments/records/{BASELINE}/plan.json")
    english_plan = read(root, f"experiments/records/{ENGLISH}/plan.json")
    routes = read(root, f"experiments/records/{BASELINE}/results.json")
    english = read(root, f"experiments/records/{ENGLISH}/results.json")
    alphabet = read(root, "data/index.json")["alphabet"]
    need([entry["index"] for entry in alphabet] == list(range(29)), "Unexpected GP29 index order")
    for name, report in ((BASELINE, routes), (ENGLISH, english)):
        need(report["plan_sha256"] == digest(root / f"experiments/records/{name}/plan.json"), "Result plan hash differs")
    need([page["page"] for page in routes["pages"]] == route_plan["pages"] == [f"lp2-{n:02d}" for n in range(56)], "Declared target pages differ")
    need(len(route_plan["openings"]) == 9 and all(len(item["indices"]) == 12 for item in route_plan["openings"]), "Fixed opening scope differs")
    need(route_plan["axes"] == ["row", "column"] and all(route_plan[name] == [False, True] for name in ("outer_reverse", "inner_reverse", "alternating")), "Declared route grid differs")
    for opening in route_plan["openings"]:
        need(digest(root / opening["source"]) == opening["sha256"], "Known-opening source hash differs")
    for entry in english_plan["inputs"]:
        need(digest(root / entry["path"]) == entry["sha256"], "English plan dependency differs")
    baseline_pages = []
    for page in routes["pages"]:
        raw = (root / "text" / (page["page"] + ".txt")).read_bytes()
        if verify_page(page, raw, alphabet, route_plan["openings"]) is not None:
            baseline_pages.append(page["page"])
    need(baseline_pages == [f"lp2-{n:02d}" for n in range(56) if n != 50], "Nonempty executed pages differ")
    need(english_plan["targets"] == baseline_pages, "English source target set differs")
    need(routes["case_count"] == sum(len(page["cases"]) for page in routes["pages"]) == 880, "Baseline case count differs")
    need(routes["matching_case_count"] == sum(bool(case["matching_openings"]) for page in routes["pages"] for case in page["cases"]) == 0, "Saved opening count differs")
    scored_pages = verify_english(english, routes["pages"], alphabet)
    for name, pages in ((BASELINE, baseline_pages), (ENGLISH, scored_pages)):
        expected = expected_metadata(name, pages)
        need(records[name].get("recorded_comparison") == expected, "Reviewed metadata differs from verified saved evidence: " + name)
        need(len(json.dumps(expected, ensure_ascii=False, separators=(",", ":"))) <= 1500, "Comparison metadata exceeds bound")
    if self_test:
        page = copy.deepcopy(next(page for page in routes["pages"] if page["page"] == "lp2-15"))
        selected = next(case for case in page["cases"] if key(case) == SETTING)
        selected["source_ordinals"][0], selected["source_ordinals"][1] = selected["source_ordinals"][1], selected["source_ordinals"][0]
        rejects(lambda: verify_page(page, (root / "text/lp2-15.txt").read_bytes(), alphabet, route_plan["openings"]), "changed source permutation")
        broken = copy.deepcopy(english)
        next(row for row in broken["observed_cases"] if row["page"] == "lp2-49")["score"] = -7.0
        rejects(lambda: verify_english(broken, routes["pages"], alphabet), "score on ineligible page")
        broken = copy.deepcopy(english)
        broken["observed_cases"].pop()
        rejects(lambda: verify_english(broken, routes["pages"], alphabet), "missing English row")
        changed = copy.deepcopy(records[BASELINE])
        changed["reproduction"]["outputs"][0]["sha256"] = "0" * 64
        rejects(lambda: verify_hashes(root, changed), "stale output hash")
    schema_checks = schema_tests(root, records) if self_test else 0
    print(json.dumps({"status": "PASS", "baseline_executed_pages": len(baseline_pages), "english_scored_pages": len(scored_pages), "generated_routes": 880, "eligible_routes": 848, "score_ineligible_pages": ["lp2-49", "lp2-55"], "empty_page": "lp2-50", "declared_hashes_checked": hashes, "fault_checks": 4 if self_test else 0, "schema_checks": schema_checks, "search_or_score_rerun": False}, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    check(args.root.resolve(), args.self_test)
