## Finding

In the pinned public corpus, **114 of 133** source-visible `.asc` files verify against the isolated Cicada public key. Eleven are key files, seven have no recognized signature block, and one produces a bad signature. A second verifier, using its own isolated keyring, agrees on every file. The source program's four checks also pass: a known signature verifies, editing its text breaks it, a foreign key does not impersonate the Cicada key, and the packet timestamp survives the edit.

The source's older table lists **228 files** because it was made from a different working-tree snapshot. The two snapshots share **123 paths**. Every shared path has the same signature result and packet time; each difference in its raw-file hash is explained exactly by LF line endings in the pinned Git blob versus CRLF in the source's working copy. The pinned snapshot has 10 paths absent from that table, and the table has 105 paths absent from pinned Git.

![Archived-only 105 paths, shared 123, pinned-only 10. The shared paths have identical verification outcomes and signature times.](experiments/records/dukotah-g02-signature-corpus/corpus-overlap.svg)

The one failing pinned copy is `ky_2013-01-opening-book-code.asc`. GnuPG reports **BADSIG** for these bytes, and this corpus has no passing copy with the same normalized body. That describes this copy; it does not establish who authored the message or whether a different authentic copy exists elsewhere.

## What the check covers

The source script scans all `.asc` files it finds in its repository, except its own `work/` control files. The pinned revision contains 135 `.asc` Git blobs; two are those excluded control files, leaving 133. We rebuilt those 133 exact path/byte pairs from Git objects, ran the pinned source script, then verified every file again through a separate GnuPG keyring. The key's full fingerprint is `6D854CD7933322A601C3286D181F01E57A35090F`; the result is about signatures under that key, not a claim that every historical Cicada message has been collected.

| Pinned file result | Files | Meaning |
|---|---:|---|
| Verified signature | 114 | GnuPG validates the signature under the specified key. |
| Public-key file | 11 | Key material, not a signed message. |
| No recognized signature | 7 | No signature block recognized by this source scan. |
| Bad signature | 1 | This exact file's signed body does not verify. |

The archive reports 55 distinct normalized signed bodies and 54 verified packet timestamps in both snapshots. These are corpus properties, not extra solved manuscript pages. In particular, a valid signature authenticates a message relative to the key; proving the key's real-world owner is a separate historical question.

## Reproduce

The [source program](experiments/records/dukotah-g02-signature-corpus/source-verify_all_signatures.py), [frozen source table](experiments/records/dukotah-g02-signature-corpus/source-archived-table.json), [pinned case manifest](experiments/records/dukotah-g02-signature-corpus/plan-frozen.json), and [new result](experiments/records/dukotah-g02-signature-corpus/fresh-table.json) are included. The 133 original file paths are preserved offline in one [content-addressed archive](experiments/records/dukotah-g02-signature-corpus/sources/asc-blobs.zip) and [path map](experiments/records/dukotah-g02-signature-corpus/sources/path-aliases.json). Duplicate files, including the two 13.5 MB interconnectedness hex copies, occupy one blob each. Rebuilding checks each file's length and SHA-256 before GnuPG runs.

From the extracted experiment bundle, run `python experiments/records/dukotah-g02-signature-corpus/check.py --replay` with GnuPG installed. It rebuilds the corpus in a temporary directory, reruns the unchanged source verifier, and independently checks all signatures in another temporary keyring. The quicker `--check` mode verifies the saved bytes, controls and snapshot comparison without invoking GnuPG. Neither mode needs the upstream repository or network.

The source code and archived table are pinned to [Dukotah/cicada3301 at `f08b20b`](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L8-provenance). This is a provenance check, not a Liber Primus decryption test.
