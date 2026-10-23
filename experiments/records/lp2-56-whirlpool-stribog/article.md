## Result

**Neither Whirlpool nor Streebog-512 matches the complete 512-bit value printed on LP2-56** for any of the 412 previously frozen artifact-byte variants. The 412 variants contain **324 distinct byte strings**. We hashed each distinct string once with each algorithm—648 digest operations—then reported every named input comparison. Whirlpool has one digest display; Streebog was compared in both ordinary byte order and the byte-reversed display used in [RFC 6986](https://www.rfc-editor.org/rfc/rfc6986.html). That yields **1,236 full-value comparisons, zero matches**. Reversing its display is a notation check, not a third algorithm.

![Whirlpool and Streebog-512 were applied to the frozen artifact bytes; all full-value comparisons missed the LP2-56 target.](experiments/records/lp2-56-whirlpool-stribog/coverage.svg)

This extends the [earlier exact-byte matrix](#/experiments/lp2-56-internal-artifact-hashes) without changing its inputs. It uses all 75 preserved manuscript JPEGs, 75 stored raw rune texts under four declared newline forms, nine stored literal sections under the same forms, and one exact 256-byte grid payload. One literal section is the printed LP2-56 hash itself, not a decoded passage. The [source plan](experiments/records/lp2-56-internal-artifact-hashes/plan.json) pins the files and byte rules; the [extension plan](experiments/records/lp2-56-whirlpool-stribog/plan.json) pins the added algorithms, controls and display rule.

## Algorithm checks

The installed **libgcrypt 1.12.2** provides both 64-byte digests. Before touching manuscript inputs, its Whirlpool output for `abc` matched the [Whirlpool reference vector reproduced in the Linux cryptographic test suite](https://android.googlesource.com/kernel/msm/+/2d94dfc8c38edf63e91e48fd55c3a8822b6a9ced/crypto/tcrypt.h). Its Streebog-512 output matched **both 512-bit examples** in [RFC 6986](https://www.rfc-editor.org/rfc/rfc6986.html#section-10). The RFC writes the message and digest as most-significant-byte-first bitstrings; their displayed bytes must be reversed to check a normal byte-oriented library call. The record pins the exact test messages and expected outputs.

The search compared the whole 64-byte digest with the whole printed value. It did not look for partial matches or adjust input bytes to make one appear. The result covers these two installed algorithm implementations and these preserved artifact bytes. It does not rule out a different source file, a keyed or salted construction, another input normalization, or older Whirlpool-0/Whirlpool-T variants.

## Reproduce

On a machine with libgcrypt, run `python experiments/records/lp2-56-whirlpool-stribog/run.py`, then `python experiments/records/lp2-56-whirlpool-stribog/check.py`. Both accept `--libgcrypt PATH` for another installation; the pinned Windows DLL is used by default when present. The runner uses the library's one-shot hash API; the checker independently reconstructs the candidate bytes and uses its streaming API. Both require all three published control vectors to pass. The [result table](experiments/records/lp2-56-whirlpool-stribog/cases.jsonl) and [summary](experiments/records/lp2-56-whirlpool-stribog/results.json) record every full comparison.
