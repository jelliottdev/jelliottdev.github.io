"""Integrate the separately frozen T3 full-book KJV receipt into its record."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REC = ROOT / "experiments/records/rune-reading-sensitivity-t3"
PATH = REC / "record.json"
PREFIX = "experiments/records/rune-reading-sensitivity-t3/"
KJV = "experiments/records/dukotah-offset-model-integrity/source-kjv.txt"


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def replace(text, old, new):
    assert old in text, (old, text)
    return text.replace(old, new, 1)


def main():
    r = json.loads(PATH.read_text(encoding="utf-8"))
    r["summary"] += " A separately recovered exact KJV input also permits the source's six-level full-book decoder replay; its results are fixture-specific."
    r["finding"] += " In the separate 12,956-rune KJV fixture (six replicates per level), median recovery first falls below 90% at k=450, when correct/wrong-key scores still separate; score distributions overlap at k=900. Fresh nested results match the archived source apart from elapsed seconds."
    r["limitations"] = replace(r["limitations"],
        "The exact full-book KJV input is unavailable, and the source dependency graph was not freshly rebuilt.",
        "The exact full-book KJV fixture was replayed, but uses a different plaintext register as well as length and has six replicates per level. The source dependency graph was not freshly rebuilt.")
    r["reader_finding"] += " In a separate full-length known-key fixture, 450 random changes reduce median recovery to 86%."
    r["reader_limit"] += " The short and full-length fixtures also use different plaintext texts."
    s = r["scope"]
    s["representation"] += " A separate 12,956-rune planted KJV passage is the full-book decoder control."
    s["procedure"] += " Replay the exact source six-level KJV full-book fixture using a recovered hash-matched input; compare every fresh result field with the pinned source output except elapsed seconds."
    s["parameters"] += " Six KJV full-book error levels [0,50,100,200,450,900] with six replicates each; optional 1–4 level-isolated replay workers."
    s["exclusions"] = replace(s["exclusions"], "full-book KJV decoder run, ", "")
    for change in r["variant"]["changes"]:
        field = change["field"]
        if field in s:
            change["after"] = s[field]
    r["review"]["reviewer"] += "; full-book KJV source-output parity"
    r["reproduction"]["environment"] += " The exact KJV corpus is a declared cross-record input; --jobs 2–4 parallelizes only independent full-book error levels."
    r["reproduction"]["script_sha256"] = sha(PREFIX + "run.py")
    inputs = r["reproduction"]["inputs"]
    bypath = {x["path"]: x for x in inputs}
    for path in (PREFIX + "plan.json", PREFIX + "fullbook-plan.json",
                 PREFIX + "out_decode_L12956_KJV.json",
                 PREFIX + "out_decode_L12956_KJV.source.json",
                 PREFIX + "replay_fullbook_parallel.py", KJV):
        bypath[path] = {"path": path, "sha256": sha(path)}
    r["reproduction"]["inputs"] = list(bypath.values())
    for item in r["reproduction"]["outputs"]:
        item["sha256"] = sha(item["path"])
    PATH.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
