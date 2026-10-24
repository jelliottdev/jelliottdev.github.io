"""Historical initial packager for the pinned G-02 source corpus.

Its first-pass independent verifier missed embedded PGP MESSAGE signatures.
The corrected reproducible path is check.py --replay and repair.py; never run
this initial packager accidentally over the corrected published record.
"""

import hashlib
import json
import shutil
import zipfile
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INTERNAL = ROOT / "research/performance/g02-pgp-2026-10-23"
TREE = ROOT.parent / "g02-pgp-replay-20261023"
LANE = "liber-primus/analysis/round18/L8-provenance"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    if "--historical-initial-pack" not in sys.argv:
        raise SystemExit("Historical initial packager is disabled; use check.py --replay and repair.py")
    plan = json.loads((INTERNAL / "plan-frozen.json").read_text(encoding="utf-8"))
    measured = json.loads((INTERNAL / "check-results.json").read_text(encoding="utf-8"))
    assert measured["independent_verdict_counts"] == {"PASS": 114, "KEY": 11, "NO-SIG": 7, "FAIL": 1}
    assert measured["common_path_byte_relation"] == {"lf_to_crlf_only": 123}
    sources = HERE / "sources"
    sources.mkdir(exist_ok=True)
    shutil.copyfile(INTERNAL / "plan-frozen.json", HERE / "plan-frozen.json")
    shutil.copyfile(INTERNAL / "materialize-receipt.json", HERE / "materialize-receipt.json")
    shutil.copyfile(INTERNAL / "check-results.json", HERE / "independent-check.json")
    shutil.copyfile(TREE / LANE / "PGP-VERIFICATION-TABLE.json", HERE / "fresh-table.json")
    shutil.copyfile(TREE / LANE / "verify_all_signatures.py", HERE / "source-verify_all_signatures.py")
    archived = ROOT.parent / "source-cache/dukotah-cicada3301" / LANE / "PGP-VERIFICATION-TABLE.json"
    shutil.copyfile(archived, HERE / "source-archived-table.json")
    prereg = ROOT.parent / "source-cache/dukotah-cicada3301" / LANE / "PREREG.md"
    shutil.copyfile(prereg, HERE / "source-PREREG.md")
    license_file = ROOT.parent / "source-cache/dukotah-cicada3301" / "LICENSE"
    shutil.copyfile(license_file, HERE / "LICENSE.source")

    aliases = []
    unique = {}
    for case in plan["cases"]:
        path = case["path"]
        if path.startswith(LANE + "/work/"):
            continue  # source code explicitly excludes its own control scratch area
        raw = (TREE / path).read_bytes()
        assert len(raw) == case["bytes"]
        sha = digest(raw)
        aliases.append({**case, "sha256": sha})
        unique.setdefault(sha, raw)
    assert len(aliases) == 133 and len(unique) == 89
    write_json(sources / "path-aliases.json", {
        "schema": "liberpedia-g02-pgp-aliases-v1",
        "source_revision": plan["source_revision"],
        "excluded_source_scratch_paths": [c["path"] for c in plan["cases"]
                                          if c["path"].startswith(LANE + "/work/")],
        "paths": aliases,
    })
    with zipfile.ZipFile(sources / "asc-blobs.zip", "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for sha, raw in sorted(unique.items()):
            z.writestr(f"blobs/{sha}", raw)
    write_json(HERE / "plan.json", {
        "schema": "liberpedia-g02-pgp-public-plan-v1",
        "frozen_plan_sha256": digest((HERE / "plan-frozen.json").read_bytes()),
        "source_revision": plan["source_revision"],
        "scope_amendment": "The frozen manifest listed all 135 committed .asc paths; the source program excludes two committed files in its own work/ scratch area, leaving 133 verification cases. This exclusion was identified after the source run and did not change the frozen manifest or any verdict.",
        "replay": "Rebuild the 133 source-visible paths from content-addressed ZIP blobs and alias manifest; run the pinned verifier under a fresh isolated GnuPG home; compare verdicts, signature times, and source controls. A separate checker verifies statuses against a different isolated keyring.",
        "limits": "This is the pinned Git corpus at f08b20b, not the 228-file historical working-tree snapshot or all Cicada messages. Signature validity alone does not prove who physically authored a message.",
    })
    write_json(HERE / "results.json", {
        "schema": "liberpedia-g02-pgp-results-v1",
        "independent_check": measured,
        "fresh_summary": json.loads((HERE / "fresh-table.json").read_text(encoding="utf-8"))["summary"],
        "archived_summary": json.loads((HERE / "source-archived-table.json").read_text(encoding="utf-8"))["summary"],
        "compressed_input_bytes": (sources / "asc-blobs.zip").stat().st_size,
        "unique_input_blobs": len(unique),
    })
    rid = "dukotah-g02-signature-corpus"
    prefix = f"experiments/records/{rid}/"
    input_names = [
        "plan-frozen.json", "plan.json", "materialize-receipt.json",
        "sources/path-aliases.json", "sources/asc-blobs.zip",
        "source-verify_all_signatures.py", "source-archived-table.json",
        "source-PREREG.md", "LICENSE.source", "check.py", "plot.py",
        "make_record.py", "article.md",
    ]
    output_names = ["fresh-table.json", "independent-check.json", "results.json", "corpus-overlap.svg"]
    items = lambda names: [{"path": prefix + n, "sha256": digest((HERE / n).read_bytes())}
                           for n in names]
    record = {
        "id": rid,
        "status": "draft",
        "title": "Which archived Cicada signatures verify?",
        "question": "Do the signed files in the pinned public Cicada corpus verify against the canonical key, and does the older source table describe the same file snapshot?",
        "reader_question": "Which archived messages have a valid Cicada signature?",
        "summary": "The pinned source scan reports 114 signatures; an all-armor GnuPG pass corrects one embedded-signature miss to 115.",
        "reader_finding": "Of 133 archived files, GnuPG verifies 115 under the specified Cicada key. The source program counted 114 because it skipped a signed PGP MESSAGE.",
        "finding": "The unchanged source scan reports 114 PASS, 11 KEY, 7 NO-SIG and 1 FAIL. Its armor-header condition skips an embedded signature in tcp-server.asc; an independent GnuPG pass reports 115 PASS, 11 KEY, 6 NO-SIG and 1 FAIL. The 123 shared paths retain the same source-program verdict and timestamp in both source snapshots.",
        "limitations": "The pinned Git corpus contains 133 source-visible .asc files; the older table used 228 working-tree files, including 105 paths missing from this commit. Signature validity is relative to the specified public key and does not itself prove historical authorship or cover all messages. This is not a Liber Primus decryption test.",
        "next_steps": "Preserve additional original signed files with their exact bytes and provenance, then rerun the same verification and compare normalized bodies and packet timestamps.",
        "outcome": "supported",
        "tags": ["Cicada 3301", "PGP", "signature verification", "provenance", "source replay"],
        "scope": {
            "pages": [],
            "artifacts": [prefix + "source-archived-table.json", prefix + "sources/asc-blobs.zip"],
            "representation": "Every .asc Git blob at pinned revision f08b20b, excluding the source verifier's own two work/ control files; exact raw bytes reconstructed from 89 content-addressed blobs at 133 paths.",
            "procedure": "Run the pinned source verifier in an isolated corpus and GnuPG home; independently verify every path with another isolated keyring; compare the saved table and source archive by path, raw SHA, signature verdict and packet time.",
            "parameters": "135 committed .asc paths, 2 source-scratch exclusions, 133 cases; canonical key fingerprint 6D854CD7933322A601C3286D181F01E57A35090F; source controls C1-C4.",
            "exclusions": "Files outside this pinned revision, unarchived signed messages, authorship beyond the public key, and any LP2 decryption hypothesis.",
        },
        "review": {"kind": "pinned-source signature replay", "retested_on": "2026-10-23",
                   "reviewer": "Source program plus independent isolated-keyring verification",
                   "human_review": "pending"},
        "reproduction": {
            "command": "python experiments/records/dukotah-g02-signature-corpus/check.py --replay",
            "environment": "Python 3 standard library and GnuPG 2.5.21 for complete offline replay; --check does not require GnuPG.",
            "script": prefix + "check.py",
            "script_sha256": digest((HERE / "check.py").read_bytes()),
            "inputs": items(input_names),
            "outputs": items(output_names),
        },
        "visuals": [{"path": prefix + "corpus-overlap.svg",
                     "caption": "The archived table and pinned Git corpus share 123 paths. Every shared path has the same signature result and packet time."}],
        "sources": [
            {"label": "Pinned G-02 source program", "url": "https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L8-provenance/verify_all_signatures.py"},
            {"label": "Archived G-02 signature table", "url": "https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L8-provenance/PGP-VERIFICATION-TABLE.json"},
            {"label": "Frozen source rules and controls", "url": "https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L8-provenance/PREREG.md"},
        ],
        "related": ["pgp-packet-keys"],
    }
    write_json(HERE / "record.json", record)
    from repair import main as apply_independent_correction
    apply_independent_correction()
    print({"paths": len(aliases), "unique_blobs": len(unique),
           "compressed_bytes": (sources / "asc-blobs.zip").stat().st_size})


if __name__ == "__main__":
    main()
