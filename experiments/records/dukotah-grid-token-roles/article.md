# Could the grid bytes be ciphertext or reading pointers?

An archived Campaign VII search tried two roles for the 256 base-60-decoded bytes from the grid on LP2-49–51: **encrypted bytes** to decode as text, or **positions** that select runes from the manuscript. We repeated its fixed operators on the archived byte list and on two later image-audited readings of disputed cells. None passed the source's stated screen in any of the three readings.

![Three grid-byte readings show best printable fractions under 47 percent and best rune-index scores below the source English-score bar.](experiments/records/dukotah-grid-token-roles/comparison.svg)

| Byte reading | Cells changed from archive | Best printable byte fraction | Best rune-index English score |
| --- | ---: | ---: | ---: |
| Archived hard-coded list | 0 | 45.2% | −7.339 |
| Six image-checked cells | 6 | 46.2% | −7.329 |
| All eleven adjudicated cells | 9 | 46.2% | −7.183 |

The byte-as-ciphertext source flagged a candidate only above **85% printable ASCII**. Its rune-index source set a **−5.0** English quadgram bar. Higher scores are more English-like under that particular model. The strongest new index score, −7.183, remains below it. These are search outcomes under fixed readings and rules; neither percentage nor quadgram score is proof about every possible payload encoding.

## Two roles, one declared byte sequence

For the ciphertext role, the source tested each token section (80, 104 and 72 bytes), their 256-byte join, and the reverse join. Each target received all **256 single-byte XOR keys**, 18 named repeating ASCII keyword XOR keys, prime, prime-minus-one, totient and Fibonacci additive streams in both signs modulo 256, and a direct read. That is **1,415 outputs per byte reading**. No output in any reading crossed the printable flag. Because none was flagged, the source's second-stage English test was never reached. The source commentary also mentions a nibble split, but its executable search does not perform one; it is outside this result.

For the pointer role, the source makes just four complete 256-rune readings: each byte as an absolute index into the joined rune corpus; each byte as a cumulative step; each byte as a position modulo a corresponding rune-bearing page; or each byte modulo 29 as a GP rune. These are **four interpretations per reading**, not 256 independent experiments. The source's page-local rule uses source rune segments 49, 50 and 51, which map to site pages LP2-49, LP2-51 and LP2-52. Those are not a demonstrated physical neighbourhood for the printed grid.

The archived program used a hard-coded list. A later [cell adjudication](#/experiments/dukotah-grid-cell-adjudication) found different printed values at six positions. Its subsequent 256-byte resolution differs at those six and three more. We preserve the archived list to reproduce its result, then change **only those bytes** for the sensitivity checks. Other plausible grid readings or routes remain untested here.

## Checks and limits

The two unmodified archived programs reproduce their saved results when placed beside their pinned dependencies in a temporary folder. A separate checker reconstructs every one of the **4,245 byte outputs** and **12 index readings** without importing those programs, verifies all three byte hashes and checks that the source rune stream matches the site transcription.

Constructed byte examples recover a complete 256-character English passage under one-byte XOR and the source prime stream. Constructed pointer examples recover the complete 85-rune documented `AN END` reading under absolute indexing, cumulative gaps and direct GP bytes; the score exceeds the source's bar. The page-local source segment 49 lacks one rune present in that reading, so that particular full positive cannot be represented by its exact lookup rule; a legal constructed page-local sequence is checked for exact recovery instead. These controls show that the implementations work on planted inputs. They do not establish that this payload carries English, or calibrate the chance of a high score after trying other conversions.

The result does not test unknown page transcriptions, arbitrary offsets, compressed streams, altered byte order beyond the declared reverse join, other books, or keys derived from later puzzle stages. It also does not make the grid a confirmed ciphertext: the index proposals are readings of bytes as pointers, without a separate decryption of LP2's runes.

## Reproduce

The [frozen plan](experiments/records/dukotah-grid-token-roles/plan.json) identifies the source revision, byte witnesses and exact screens. [Results](experiments/records/dukotah-grid-token-roles/results.json) contain all maxima, four index scores per witness, controls and changed-cell positions. Run from a Liberpedia checkout:

```text
python experiments/records/dukotah-grid-token-roles/run.py --check
python experiments/records/dukotah-grid-token-roles/check.py
python experiments/records/dukotah-grid-token-roles/plot.py --check
```

The replay uses the pinned [ciphertext-role program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/token_as_ciphertext.py) and [index-role program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/token_as_index.py). Their original saved outputs predate this test. The two corrected-byte sensitivity runs and independent controls are added here.
