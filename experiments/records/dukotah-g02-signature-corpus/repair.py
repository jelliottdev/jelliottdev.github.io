"""Reconcile the source table with GnuPG's complete all-armor verification.

The original source table, source program, input archive and frozen plan stay
byte-for-byte unchanged. Run check.py --refresh-independent before this script.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "experiments/records/dukotah-g02-signature-corpus/"
EMBEDDED = "corpus/A-primary-artifacts/ibotpeaches/messages/2013/tcp-server.asc"


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8", newline="\n")


def digest(name):
    return hashlib.sha256((HERE / name).read_bytes()).hexdigest()


def main():
    independent = read("independent-verification.json")
    assert independent["files_attempted_with_gpg"] == 133
    assert independent["by_gpg_verdict"] == {"FAIL": 1, "KEY": 11, "NO-SIG": 6, "PASS": 115}
    assert independent["source_verdict_differences"] == [EMBEDDED]
    check = read("independent-check.json")
    check["independent_verdict_counts"] = independent["by_gpg_verdict"]
    check["independent_verdict_mismatches"] = [EMBEDDED]
    check["independent_distinct_verified_timestamps"] = independent["distinct_verified_timestamps"]
    check["independent_all_armor_attempted"] = 133
    check["independent_message_signature_note"] = "The pinned source parser skipped an embedded signature in tcp-server.asc; all 133 files were submitted to GnuPG independently."
    write("independent-check.json", check)
    results = read("results.json")
    results["independent_check"] = check
    results["independent_verification_summary"] = {
        k: independent[k] for k in ("files_attempted_with_gpg", "by_gpg_verdict",
                                     "source_verdict_differences", "distinct_verified_timestamps")}
    write("results.json", results)
    record = read("record.json")
    record["summary"] = ("GnuPG verifies 115 signatures in the pinned 133-file corpus. "
                         "The source program reported 114 because it missed one signature embedded in a PGP MESSAGE; "
                         "its older and newer tables still agree on their 123 shared paths.")
    record["reader_finding"] = ("Of 133 archived files, GnuPG verifies 115 under the specified Cicada key. "
                                "The source program counted 114 because it skipped a signed PGP MESSAGE. "
                                "One separate malformed copy fails; its repaired copy and the original JPEG extraction verify.")
    record["finding"] = ("The unchanged source program reports 114 PASS, 11 KEY, 7 NO-SIG and 1 FAIL. "
                         "An independent GnuPG pass over every file finds 115 PASS, 11 KEY, 6 NO-SIG and 1 FAIL. "
                         "The sole difference is tcp-server.asc, whose PGP MESSAGE contains a valid embedded signature. "
                         "The two source-program snapshots agree on all 123 shared paths, with only LF/CRLF byte differences.")
    record["limitations"] = ("The pinned Git corpus contains 133 source-visible .asc files; the older table used 228 working-tree files, "
                             "including 105 paths missing from this commit. The source program's armor-header heuristic misses "
                             "embedded signatures, so its 114/7 counts are not the corrected GnuPG verdicts. Validity under the "
                             "specified public key does not prove historical authorship or cover all messages; this is not an LP2 decryption test.")
    record["scope"]["procedure"] = ("Run the pinned source verifier unchanged in an isolated corpus. Separately submit all 133 exact "
                                      "files to GnuPG under a fresh canonical-key-only home, including armored PGP MESSAGE packets; "
                                      "compare source versus independent verdicts and the two source snapshots by path and bytes.")
    record["visuals"][0]["caption"] = ("The archived table and pinned Git corpus share 123 paths. Their source-program verdicts "
                                         "and extracted times agree; the independent GnuPG pass corrects one shared-path verdict.")
    record["reproduction"]["environment"] = ("Python 3 standard library and GnuPG for full offline replay; "
                                                  "--check validates the saved all-armor receipt without GnuPG.")
    ins = record["reproduction"]["inputs"]
    outs = record["reproduction"]["outputs"]
    if not any(x["path"].endswith("/repair.py") for x in ins):
        ins.append({"path": PREFIX + "repair.py", "sha256": ""})
    if not any(x["path"].endswith("/independent-verification.json") for x in outs):
        outs.append({"path": PREFIX + "independent-verification.json", "sha256": ""})
    for item in ins + outs:
        name = item["path"].removeprefix(PREFIX)
        item["sha256"] = digest(name)
    record["reproduction"]["script_sha256"] = digest("check.py")
    write("record.json", record)
    print("Reconciled GPG 115/6 versus source 114/7; refreshed record dependency hashes")


if __name__ == "__main__":
    main()
