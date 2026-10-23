"""Compare fresh Stage B summary to the pinned source's archived result."""
import collections
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SOURCE_RESULT = pathlib.Path(
    "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301/liber-primus/analysis/round13/B04/results_B.json")
FRESH = pathlib.Path(
    "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/b04-lp2-B-20261023/merged.json")


def compare():
    original = json.loads(SOURCE_RESULT.read_text(encoding="utf-8"))
    fresh = json.loads(FRESH.read_text(encoding="utf-8"))[
        "source_stage_summary"]
    fields = [key for key in original if key not in ("elapsed_s", "rate_per_s", "top50")]
    matches = {key: original[key] == fresh[key] for key in fields}
    if not all(matches.values()):
        raise AssertionError("archived source Stage B fields differ: " +
                             repr([key for key, match in matches.items() if not match]))
    encode = lambda row: json.dumps(row, ensure_ascii=True, sort_keys=True)
    same_multiset = (collections.Counter(map(encode, original["top50"])) ==
                     collections.Counter(map(encode, fresh["top50"])))
    same_scores = ([row["score"] for row in original["top50"]] ==
                   [row["score"] for row in fresh["top50"]])
    assert same_multiset and same_scores
    return {"schema": "b04-stage-b-source-result-parity-v1",
            "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
            "source_result_sha256": hashlib.sha256(SOURCE_RESULT.read_bytes()).hexdigest(),
            "fresh_merged_sha256": hashlib.sha256(FRESH.read_bytes()).hexdigest(),
            "all_non_runtime_fields_match_except_tie_order": True,
            "top50_same_multiset": same_multiset,
            "top50_score_order_same": same_scores,
            "top50_exact_order_same": original["top50"] == fresh["top50"],
            "tie_note": "Equal-score rows can exchange order under unordered worker completion; the same 50 rows and score order were recovered."}


if __name__ == "__main__":
    result = compare()
    (HERE / "source-result-parity.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
