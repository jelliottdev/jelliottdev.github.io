## Result

**None of the 1,236 declared hash comparisons equals the 512-bit value printed on LP2-56.** This covers 412 byte candidates and three algorithms. Some text variants produce identical bytes, so there are **324 distinct input byte strings**. The result is a narrow check of these preserved files, not a test of every possible message, encoding or file associated with Cicada 3301.

![Four input families compared under three 512-bit hashes; no exact matches.](experiments/records/lp2-56-internal-artifact-hashes/coverage.svg)

The printed target occupies **five rows totaling 128 hexadecimal characters**, or 64 bytes. It is a plausible digest length but the page does not identify a hash function or an input. Testing a digest requires both. A suggested input chosen after looking at the target creates an unbounded search, so this record fixed a finite set before computing matches.

## What went into the check

| Input | Byte rule | Candidates |
| --- | --- | ---: |
| Original manuscript images | Exact bytes of all 75 archived JPEGs | 75 |
| Rune transcriptions | Each of the 75 stored `raw` strings encoded as UTF-8 | 300 variants |
| Stored literal sections | Nine sections made by joining their stored `reading.literal` strings in page order | 36 variants |
| Resolved grid payload | Exact 256-byte payload already extracted in the LP2-54 source replay | 1 |

The nine literal sections include **LP2-56's printed hash text itself**; that entry is an inventory check, not a decoded passage. The other eight are readings. The text counts include four stated byte forms per string: exact UTF-8; LF changed to CRLF; one final LF removed if present; and exactly one final LF ensured. The two cover-page rune strings are empty; they remain in the audit so the inventory is complete. No text was translated, respelled, uppercased, padded or reinterpreted as hexadecimal. Each candidate was hashed with **SHA-512, SHA3-512 and BLAKE2b-512** and compared byte for byte with the printed target.

This revisits a public proposal to hash the page JPEGs under SHA-512 and BLAKE2b. Its saved source table reports 75 values for each algorithm, but did not preserve the source JPEG bytes. This check uses Liberpedia's preserved originals, whose exact SHA-256 values are pinned in the [input plan](experiments/records/lp2-56-internal-artifact-hashes/plan.json). It adds the other declared local artifacts; it does not equate two image sets whose byte identity was not established.

**Whirlpool and Streebog were not run.** No trusted implementation with a verified control vector was available in this environment. A failure to find a match among the three run algorithms says nothing about either excluded algorithm, a different file, a URL response, or an undisclosed byte transformation.

## Reproduce

From the repository root, run `python experiments/records/lp2-56-internal-artifact-hashes/run.py` to recreate the [1,236-row digest table](experiments/records/lp2-56-internal-artifact-hashes/cases.jsonl) and [summary](experiments/records/lp2-56-internal-artifact-hashes/results.json). Then run `python experiments/records/lp2-56-internal-artifact-hashes/check.py`. The checker independently reconstructs every input byte string and digest, verifies source-file hashes and standard `abc` algorithm vectors, and checks the 64-byte target extraction. Both use Python's standard library.
