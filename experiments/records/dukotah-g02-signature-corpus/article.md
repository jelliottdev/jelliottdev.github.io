## Finding

GnuPG verifies **115 of the 133** `.asc` files in the pinned corpus against the Cicada public key. The original source program reported **114**. It missed one valid signature inside `tcp-server.asc` because it only sent files containing the literal `BEGIN PGP SIGNATURE` header to GnuPG. This file is an armored **PGP MESSAGE** with an embedded signature packet; GnuPG reports `VALIDSIG` for the canonical fingerprint. Our independent pass sent all 133 files to GnuPG, including the 11 public-key files. The remaining classifications are 11 key files, six without a verified signature, and one bad signature.

The source program's four controls still pass: a known signature verifies, editing its text breaks it, a foreign key does not impersonate the Cicada key, and the packet timestamp survives the edit. They did not include an embedded-signature PGP MESSAGE. We preserve the source's **114 verified / 7 unsigned** result in its original table and report the corrected **115 / 6** separately.

The source's older table lists **228 files** because it was made from a different working-tree snapshot. The two snapshots share **123 paths**. Every shared path has the same *source-program* verdict and extracted packet time; the old table shares the same blind spot for `tcp-server.asc`. Each difference in a shared path's raw-file hash is explained exactly by LF line endings in the pinned Git blob versus CRLF in the source's working copy. The pinned snapshot has 10 paths absent from that table, and the table has 105 paths absent from pinned Git.

![Archived-only 105 paths, shared 123, pinned-only 10. The shared paths have identical source-program verdicts and extracted times.](experiments/records/dukotah-g02-signature-corpus/corpus-overlap.svg)

The one **BADSIG** is a malformed copy of the [2013 opening message](#/wiki/2013-opening): `ky_2013-01-opening-book-code.asc` is missing the blank line after `Hash: SHA1`. Inserting that one line produces the corpus's repaired copy, which **verifies**. Another corpus copy and the [payload freshly extracted from the preserved 2013 JPEG](experiments/records/dukotah-g02-signature-corpus/source-2013-jpeg-extraction.asc) also verify under the same key. All four contain identical signature-packet bytes. The JPEG payload differs from the repaired copy only by one trailing space in the riddle and a final newline; the three passing copies have the same signed text after OpenPGP's trailing-whitespace handling. The bad armor has no validly parsed signed body until its header separator is restored.

The source's “no passing twin” label came from its body extractor: it split the malformed file at the first blank line, thereby dropping “Welcome again.” and assigning it a different fingerprint. The source's **55 body fingerprints** include that artifact; **54** occur among files its parser verified. GnuPG independently finds **55 distinct valid signature times** in the pinned files after including the embedded signature. We preserve the original bad bytes and source verdict rather than replacing them with the repaired version. A valid signature confirms the message relative to this public key, not the key holder's real-world identity.

## What the check covers

The source script scans all `.asc` files it finds in its repository, except its own `work/` control files. The pinned revision contains 135 `.asc` Git blobs; two are those excluded control files, leaving 133. We rebuilt those 133 exact path/byte pairs from Git objects and reran the pinned source script unchanged. The independent checker then asked GnuPG to verify **all 133**, instead of deciding from armor text which files to send. The key's full fingerprint is `6D854CD7933322A601C3286D181F01E57A35090F`; the result is about signatures under that key, not a claim that every historical Cicada message has been collected.

| Independent GnuPG result | Files | Meaning |
|---|---:|---|
| Verified signature | 115 | GnuPG validates the signature under the specified key, including the embedded signature. |
| Public-key file | 11 | Key material, not a signed message. |
| No verified signature | 6 | No valid signature under this key was found. |
| Bad signature | 1 | This exact file's signed body does not verify. |

The [per-file independent receipt](experiments/records/dukotah-g02-signature-corpus/independent-verification.json) records both verdicts and the GnuPG status for the one disagreement. These are corpus properties, not extra solved manuscript pages.

## Reproduce

The [source program](experiments/records/dukotah-g02-signature-corpus/source-verify_all_signatures.py), [frozen source table](experiments/records/dukotah-g02-signature-corpus/source-archived-table.json), [pinned case manifest](experiments/records/dukotah-g02-signature-corpus/plan-frozen.json), and [new result](experiments/records/dukotah-g02-signature-corpus/fresh-table.json) are included. The 133 original file paths are preserved offline in one [content-addressed archive](experiments/records/dukotah-g02-signature-corpus/sources/asc-blobs.zip) and [path map](experiments/records/dukotah-g02-signature-corpus/sources/path-aliases.json). Duplicate files, including the two 13.5 MB interconnectedness hex copies, occupy one blob each. Rebuilding checks each file's length and SHA-256 before GnuPG runs. The separately preserved [JPEG extraction](experiments/records/dukotah-g02-signature-corpus/source-2013-jpeg-extraction.asc) and [opening-copy receipt](experiments/records/dukotah-g02-signature-corpus/opening-crosscheck.json) document the one-line repair, canonical text and isolated GPG verdicts without changing the 133-case source scan.

From the extracted experiment bundle, run `python experiments/records/dukotah-g02-signature-corpus/check.py --replay` with GnuPG installed. It rebuilds the corpus in a temporary directory, reruns the unchanged source verifier, and independently asks GnuPG about all 133 files and the four opening variants in isolated keyrings. The quicker `--check` mode verifies the saved bytes, both sets of verdicts, controls, opening-copy relationships and snapshot comparison without invoking GnuPG. Neither mode needs the upstream repository or network.

The source code and archived table are pinned to [Dukotah/cicada3301 at `f08b20b`](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L8-provenance). This is a provenance check, not a Liber Primus decryption test.
