"""Verify saved G-02 results and optionally rerun every signature offline.

The content-addressed archive restores every original path, including duplicate copies,
without any network access or Git checkout.  `--replay` requires GnuPG on PATH.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = "liber-primus/analysis/round18/L8-provenance"
KEY = "corpus/A-primary-artifacts/pgp/keys/cicada-3301-pubkey.keyserver.ubuntu.com.asc"


def j(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_blobs():
    aliases = j("sources/path-aliases.json")
    assert aliases["schema"] == "liberpedia-g02-pgp-aliases-v1"
    assert len(aliases["paths"]) == 133
    assert len(aliases["excluded_source_scratch_paths"]) == 2
    data = {}
    with zipfile.ZipFile(HERE / "sources/asc-blobs.zip") as z:
        assert len(z.namelist()) == 89
        for a in aliases["paths"]:
            label = f"blobs/{a['sha256']}"
            raw = z.read(label)
            assert len(raw) == a["bytes"] and sha(raw) == a["sha256"], a["path"]
            data[a["path"]] = raw
    assert len(data) == 133
    return data


def table_comparison(raw_by_path, fresh, archived):
    a = {x["path"]: x for x in archived["rows"]}
    f = {x["path"]: x for x in fresh["rows"]}
    assert set(raw_by_path) == set(f)
    relation = collections.Counter()
    verdict_mismatch = []
    time_mismatch = []
    for p in set(a) & set(f):
        raw = raw_by_path[p]
        if sha(raw) == a[p]["sha256"]:
            relation["exact"] += 1
        elif sha(raw.replace(b"\n", b"\r\n")) == a[p]["sha256"]:
            relation["lf_to_crlf_only"] += 1
        else:
            relation["other_byte_change"] += 1
        if a[p]["verdict"] != f[p]["verdict"]:
            verdict_mismatch.append(p)
        if a[p]["signature_timestamp_unix"] != f[p]["signature_timestamp_unix"]:
            time_mismatch.append(p)
    return {
        "fresh_files_scanned": len(f),
        "archived_files_scanned": len(a),
        "paths_common": len(set(a) & set(f)),
        "paths_only_archived": len(set(a) - set(f)),
        "paths_only_fresh": len(set(f) - set(a)),
        "common_path_byte_relation": dict(relation),
        "common_path_verdict_mismatches": sorted(verdict_mismatch),
        "common_path_signature_time_mismatches": sorted(time_mismatch),
    }


def gpg(home, args):
    env = dict(os.environ, LC_ALL="C", TZ="UTC")
    return subprocess.run(["gpg", "--homedir", str(home), "--batch", "--no-tty", *args],
                          capture_output=True, text=True, env=env, timeout=60)


def independent_verdicts(tree, raw_by_path):
    canon = j("plan-frozen.json")["canonical_fingerprint"]
    with tempfile.TemporaryDirectory(prefix="g02-independent-") as h:
        home = Path(h)
        imported = gpg(home, ["--import", str(tree / KEY)])
        assert imported.returncode == 0, imported.stderr
        listing = gpg(home, ["--with-colons", "--fingerprint", "--list-keys"])
        fprs = [l.split(":")[9] for l in listing.stdout.splitlines() if l.startswith("fpr:")]
        assert canon in fprs
        verdicts = {}
        for path, raw in sorted(raw_by_path.items()):
            if b"BEGIN PGP PUBLIC KEY BLOCK" in raw[:400] and b"BEGIN PGP SIGNATURE" not in raw:
                verdict = "KEY"
            elif b"BEGIN PGP SIGNATURE" not in raw:
                verdict = "NO-SIG"
            else:
                result = gpg(home, ["--status-fd", "1", "--verify", str(tree / path)])
                fpr = re.search(r"\[GNUPG:\] VALIDSIG ([0-9A-F]+)", result.stdout)
                verdict = "PASS" if fpr and fpr.group(1) == canon else "FAIL"
            verdicts[path] = verdict
    return verdicts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check packaged bytes and saved results")
    parser.add_argument("--replay", action="store_true", help="Run pinned source and independent GnuPG checks")
    args = parser.parse_args()
    assert not (args.check and args.replay)
    plan = j("plan-frozen.json")
    public_plan = j("plan.json")
    assert sha((HERE / "plan-frozen.json").read_bytes()) == public_plan["frozen_plan_sha256"]
    assert sha((HERE / "source-verify_all_signatures.py").read_bytes()) == plan["source_program"]["sha256"]
    assert sha((HERE / "source-archived-table.json").read_bytes()) == plan["source_table"]["sha256"]
    raw_by_path = read_blobs()
    fresh, archived, results = j("fresh-table.json"), j("source-archived-table.json"), j("results.json")
    check = table_comparison(raw_by_path, fresh, archived)
    evidence = results["independent_check"]
    for k, v in check.items():
        assert evidence[k] == v, k
    assert fresh["instrument_controls"]["all_met"]
    assert collections.Counter(x["verdict"] for x in fresh["rows"]) == {
        "PASS": 114, "KEY": 11, "NO-SIG": 7, "FAIL": 1}
    assert fresh["summary"]["distinct_message_bodies"] == archived["summary"]["distinct_message_bodies"] == 55
    assert fresh["summary"]["distinct_verified_timestamps"] == archived["summary"]["distinct_verified_timestamps"] == 54
    assert check["paths_common"] == 123
    assert check["common_path_byte_relation"] == {"lf_to_crlf_only": 123}
    assert not check["common_path_verdict_mismatches"] and not check["common_path_signature_time_mismatches"]

    if args.replay:
        with tempfile.TemporaryDirectory(prefix="g02-replay-") as t:
            tree = Path(t)
            for path, raw in raw_by_path.items():
                dest = tree / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
            script = tree / LANE / "verify_all_signatures.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_bytes((HERE / "source-verify_all_signatures.py").read_bytes())
            with tempfile.TemporaryDirectory(prefix="g02-gpg-") as scratch:
                child_env = dict(os.environ, TMPDIR=scratch, TEMP=scratch, TMP=scratch)
                source_run = subprocess.run([os.sys.executable, str(script)], cwd=tree,
                                            capture_output=True, text=True, timeout=180,
                                            env=child_env)
            assert source_run.returncode == 0, source_run.stderr
            replay = json.loads((tree / LANE / "PGP-VERIFICATION-TABLE.json").read_text(encoding="utf-8"))
            replay_rows = {x["path"]: x for x in replay["rows"]}
            saved_rows = {x["path"]: x for x in fresh["rows"]}
            assert set(replay_rows) == set(saved_rows)
            assert replay["instrument_controls"]["all_met"], replay["instrument_controls"]
            for path, row in saved_rows.items():
                for field in ("sha256", "verdict", "signature_timestamp_unix", "signing_keyid_from_packet"):
                    assert row[field] == replay_rows[path][field], (path, field)
            independent = independent_verdicts(tree, raw_by_path)
            assert all(independent[p] == row["verdict"] for p, row in saved_rows.items())
        print("PASS: offline source rerun and separate GnuPG keyring verified all 133 paths")
    else:
        print("PASS: 133 archived inputs, 123 shared-path reconciliations and saved control evidence")


if __name__ == "__main__":
    main()
