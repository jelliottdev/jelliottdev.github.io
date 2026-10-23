"""Independent per-file GnuPG replay and source-table reconciliation for G-02."""

import collections
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TREE = ROOT.parent / "g02-pgp-replay-20261023"
SOURCE = ROOT.parent / "source-cache" / "dukotah-cicada3301"
PLAN = json.loads((HERE / "plan-frozen.json").read_text(encoding="utf-8"))
LANE = "liber-primus/analysis/round18/L8-provenance"
FRESH = TREE / LANE / "PGP-VERIFICATION-TABLE.json"
CANON = PLAN["canonical_fingerprint"]
KEY = "corpus/A-primary-artifacts/pgp/keys/cicada-3301-pubkey.keyserver.ubuntu.com.asc"


def gpg(home, args):
    env = dict(os.environ, LC_ALL="C", TZ="UTC")
    return subprocess.run(["gpg", "--homedir", str(home), "--batch", "--no-tty", *args],
                          capture_output=True, text=True, env=env, timeout=60)


def source_blob(path):
    return subprocess.run(["git", "show", f"{PLAN['source_revision']}:{path}"],
                          cwd=SOURCE, check=True, capture_output=True).stdout


def main():
    fresh = json.loads(FRESH.read_text(encoding="utf-8"))
    archive = json.loads(source_blob(PLAN["source_table"]["path"]))
    expected_cases = {x["path"]: x for x in PLAN["cases"]
                      if not x["path"].startswith(LANE + "/work/")}
    assert len(expected_cases) == 133
    fresh_rows = {x["path"]: x for x in fresh["rows"]}
    archive_rows = {x["path"]: x for x in archive["rows"]}
    assert set(fresh_rows) == set(expected_cases)
    exact_pinned = 0
    bad = []
    for path, spec in expected_cases.items():
        local = (TREE / path).read_bytes()
        pinned = source_blob(path)
        if local == pinned and len(local) == spec["bytes"]:
            exact_pinned += 1
        else:
            bad.append(path)
    assert not bad

    with tempfile.TemporaryDirectory(prefix="g02-check-") as h:
        home = Path(h)
        imp = gpg(home, ["--import", str(TREE / KEY)])
        assert imp.returncode == 0, imp.stderr
        listing = gpg(home, ["--with-colons", "--fingerprint", "--list-keys"])
        fprs = [l.split(":")[9] for l in listing.stdout.splitlines() if l.startswith("fpr:")]
        assert CANON in fprs
        verdicts = collections.Counter()
        independent_mismatch = []
        for path, row in sorted(fresh_rows.items()):
            raw = (TREE / path).read_bytes()
            if b"BEGIN PGP PUBLIC KEY BLOCK" in raw[:400] and b"BEGIN PGP SIGNATURE" not in raw:
                verdict = "KEY"
            elif b"BEGIN PGP SIGNATURE" not in raw:
                verdict = "NO-SIG"
            else:
                proc = gpg(home, ["--status-fd", "1", "--verify", str(TREE / path)])
                fpr = re.search(r"\[GNUPG:\] VALIDSIG ([0-9A-F]+)", proc.stdout)
                verdict = "PASS" if fpr and fpr.group(1) == CANON else "FAIL"
            verdicts[verdict] += 1
            if verdict != row["verdict"]:
                independent_mismatch.append({"path": path, "independent": verdict,
                                             "source": row["verdict"]})
        assert not independent_mismatch, independent_mismatch

    common = set(fresh_rows) & set(archive_rows)
    changes = collections.Counter()
    verdict_mismatches = []
    timestamp_mismatches = []
    for path in common:
        raw = (TREE / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() == archive_rows[path]["sha256"]:
            changes["exact"] += 1
        elif hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest() == archive_rows[path]["sha256"]:
            changes["lf_to_crlf_only"] += 1
        else:
            changes["other_byte_change"] += 1
        if fresh_rows[path]["verdict"] != archive_rows[path]["verdict"]:
            verdict_mismatches.append(path)
        if fresh_rows[path]["signature_timestamp_unix"] != archive_rows[path]["signature_timestamp_unix"]:
            timestamp_mismatches.append(path)
    result = {
        "schema": "liberpedia-g02-pgp-check-v1",
        "source_revision": PLAN["source_revision"],
        "plan_sha256": hashlib.sha256((HERE / "plan-frozen.json").read_bytes()).hexdigest(),
        "pinned_case_bytes_exact": exact_pinned,
        "source_program_controls_pass": fresh["instrument_controls"]["all_met"],
        "fresh_files_scanned": len(fresh_rows),
        "independent_verdict_counts": dict(verdicts),
        "independent_verdict_mismatches": independent_mismatch,
        "archived_files_scanned": len(archive_rows),
        "paths_common": len(common),
        "paths_only_archived": len(set(archive_rows) - set(fresh_rows)),
        "paths_only_fresh": len(set(fresh_rows) - set(archive_rows)),
        "common_path_byte_relation": dict(changes),
        "common_path_verdict_mismatches": verdict_mismatches,
        "common_path_signature_time_mismatches": timestamp_mismatches,
        "fresh_distinct_message_bodies": fresh["summary"]["distinct_message_bodies"],
        "archived_distinct_message_bodies": archive["summary"]["distinct_message_bodies"],
        "fresh_distinct_verified_timestamps": fresh["summary"]["distinct_verified_timestamps"],
        "archived_distinct_verified_timestamps": archive["summary"]["distinct_verified_timestamps"],
    }
    assert changes["other_byte_change"] == 0
    assert not verdict_mismatches and not timestamp_mismatches
    out = HERE / "check-results.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
