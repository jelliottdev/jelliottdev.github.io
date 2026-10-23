## Finding

In the pinned public corpus, **114 of 133** source-visible `.asc` files verify against the isolated Cicada public key. Eleven are key files, seven have no recognized signature block, and one produces a bad signature. A second verifier, using its own isolated keyring, agrees on every file. The source program's four checks also pass: a known signature verifies, editing its text breaks it, a foreign key does not impersonate the Cicada key, and the packet timestamp survives the edit.

The source's older table lists **228 files** because it was made from a different working-tree snapshot. The two snapshots share **123 paths**. Every shared path has the same signature result and packet time; each difference in its raw-file hash is explained exactly by LF line endings in the pinned Git blob versus CRLF in the source's working copy. The pinned snapshot has 10 paths absent from that table, and the table has 105 paths absent from pinned Git.

![Archived-only 105 paths, shared 123, pinned-only 10. The shared paths have identical verification outcomes and signature times.](experiments/records/dukotah-g02-signature-corpus/corpus-overlap.svg)

The one **BADSIG** is a malformed copy of the [2013 opening message](#/wiki/2013-opening): `ky_2013-01-opening-book-code.asc` is missing the blank line after `Hash: SHA1`. Inserting that one line produces the corpus's repaired copy, which **verifies**. Another corpus copy and the [payload freshly extracted from the preserved 2013 JPEG](experiments/records/dukotah-g02-signature-corpus/source-2013-jpeg-extraction.asc) also verify under the same key. All four contain identical signature-packet bytes. The JPEG payload differs from the repaired copy only by one trailing space in the riddle and a final newline; the three passing copies have the same signed text after OpenPGP's trailing-whitespace handling. The bad armor has no validly parsed signed body until its header separator is restored.

The source's “no passing twin” label came from its body extractor: it split the malformed file at the first blank line, thereby dropping “Welcome again.” and assigning it a different fingerprint. The source's **55 body fingerprints** include that artifact; **54** occur among verified files. We preserve the original bad bytes and source verdict rather than replacing them with the repaired version. A valid signature confirms the message relative to this public key, not the key holder's real-world identity.

## What the check covers

The source script scans all `.asc` files it finds in its repository, except its own `work/` control files. The pinned revision contains 135 `.asc` Git blobs; two are those excluded control files, leaving 133. We rebuilt those 133 exact path/byte pairs from Git objects, ran the pinned source script, then verified every file again through a separate GnuPG keyring. The key's full fingerprint is `6D854CD7933322A601C3286D181F01E57A35090F`; the result is about signatures under that key, not a claim that every historical Cicada message has been collected.

| Pinned file result | Files | Meaning |
|---|---:|---|
| Verified signature | 114 | GnuPG validates the signature under the specified key. |
| Public-key file | 11 | Key material, not a signed message. |
| No recognized signature | 7 | No signature block recognized by this source scan. |
| Bad signature | 1 | This exact file's signed body does not verify. |

The source extractor reports 55 body fingerprints and 54 verified packet timestamps in both snapshots. The malformed opening copy accounts for one fingerprint that is absent from all verified files. These are corpus properties, not extra solved manuscript pages.

## Reproduce

The [source program](experiments/records/dukotah-g02-signature-corpus/source-verify_all_signatures.py), [frozen source table](experiments/records/dukotah-g02-signature-corpus/source-archived-table.json), [pinned case manifest](experiments/records/dukotah-g02-signature-corpus/plan-frozen.json), and [new result](experiments/records/dukotah-g02-signature-corpus/fresh-table.json) are included. The 133 original file paths are preserved offline in one [content-addressed archive](experiments/records/dukotah-g02-signature-corpus/sources/asc-blobs.zip) and [path map](experiments/records/dukotah-g02-signature-corpus/sources/path-aliases.json). Duplicate files, including the two 13.5 MB interconnectedness hex copies, occupy one blob each. Rebuilding checks each file's length and SHA-256 before GnuPG runs. The separately preserved [JPEG extraction](experiments/records/dukotah-g02-signature-corpus/source-2013-jpeg-extraction.asc) and [opening-copy receipt](experiments/records/dukotah-g02-signature-corpus/opening-crosscheck.json) document the one-line repair, canonical text and isolated GPG verdicts without changing the 133-case source scan.

From the extracted experiment bundle, run `python experiments/records/dukotah-g02-signature-corpus/check.py --replay` with GnuPG installed. It rebuilds the corpus in a temporary directory, reruns the unchanged source verifier, and independently checks all signatures and the four opening variants in isolated keyrings. The quicker `--check` mode verifies the saved bytes, controls, opening-copy relationships and snapshot comparison without invoking GnuPG. Neither mode needs the upstream repository or network.

The source code and archived table are pinned to [Dukotah/cicada3301 at `f08b20b`](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L8-provenance). This is a provenance check, not a Liber Primus decryption test.
