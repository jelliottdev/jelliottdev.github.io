# Rotation, hash and cuneiform keys

**Finding.** Three archived Campaign VII programs tried fixed numerical key streams: a 13-value rotation sequence attributed to the 2012 puzzle, several streams derived from the **512-bit value printed on LP2-56**, and five short number sequences labelled cuneiform or base-60. We reran all three programs and independently checked every one of their **5,376 fixed settings**. **None reached the programs’ −5.2 English-score bar.** This is a result for the listed key constructions and clocks, not a test of every number-based cipher.

![The best result in each of three fixed numeric-key searches remains below the archived score bar.](experiments/records/dukotah-fixed-numeric-keys/comparison.svg)

| Fixed key group | Manuscript settings | Best score | Best page | Above −5.2 |
| --- | ---: | ---: | --- | ---: |
| 2012 rotation sequence, forward or reversed | 896 | −6.895 | LP2-22 | 0 |
| LP2-56 hash bytes, digits or digest expansions | 2,240 | −6.679 | LP2-49 | 0 |
| Cuneiform values, `1033`, `3301` and their combination | 2,240 | −6.725 | LP2-51 | 0 |

The page names above are **image page labels**. The third program calls its best target `p50`, because its source numbers only pages containing runes; LP2-50 has a number grid but no rune transcription. That source `p50` is **LP2-51**, not the grid page.

## What these searches cover

All three programs use the same operation: take each rune’s alphabet index (0–28), optionally reflect it by Atbash, then add or subtract the next fixed key value modulo 29. For the second clock, a ciphertext `ᚠ` is copied as literal **F** and does not consume a key value. Each key begins at position zero on a page, or at position zero for the joined 55-page stream. The complete stream is scored by a pinned English four-letter frequency model.

The first program tries the source’s 13-number rotation sequence in both directions. Its historical attribution comes from the source; this replay tests the **listed values**, not the provenance of that clue. The second program starts with the printed LP2-56 hexadecimal value and tries its bytes, its individual hexadecimal digits, SHAKE-256 output, and iterative SHA-512 or BLAKE2b digest chains. We checked that its 128-character input matches the five printed rows in the site’s LP2-56 transcription. The third program tries the literal four-value list `17, 13, 55, 1`, its reverse, the digits of `1033` and `3301`, and one twelve-value concatenation. The source says the short four-value lists fall within a generic short-key search; **the twelve-value concatenation does not follow from a length-four search**.

Every named stream is tested on **55 rune-bearing LP2-00–55 pages and their joined stream**, with two signs, two Atbash choices and both F clocks. The independent page comparison found no rune-order difference between the pinned source and those 55 Liberpedia page records. Each original program reruns to exactly the JSON result preserved beside its source; the separate checker rebuilds the **score and complete output hash for every setting**.

## A score is a screen, not a solved page

We checked whether this screen can recognize known text under the same transforms. The controls use the full 85-rune LP2-56 reading, the 184-rune known warning reading, and a deterministic 277-rune repetition of the first. All **288 constructed messages decode exactly** under their chosen rule. All **144** controls that advance the key on every rune score above −5.2. In the literal-F clock, **141 of 144** do. Each of the 96 key/sign/Atbash/clock branches passes the score bar with at least two of the three messages.

The literal-F rule has a constraint: if a key setting would need ciphertext F for a non-F plaintext rune, that rune cannot be encoded unchanged, because the decoder always copies F literally. For that control we put a known literal F at the affected position *before scoring* and verify the exact constructed message. It is **not** a claim that the original LP2-56 or warning reading survives unchanged in all F-clock settings. The three below-bar plants show the fixed score threshold can miss a correct output under particular combinations; a no-hit manuscript score is consequently narrower than a proof that the key is impossible.

These runs do not test another rotation order, another hash or derivation, a key phase chosen from page artwork, other interpretations of the cuneiform marks, or a changing rule across pages. The source’s −5.2 bar is a heuristic English screen, not a probability estimate or a guarantee of decryption.

## Reproduce

The [plan frozen before our local manuscript rerun](experiments/records/dukotah-fixed-numeric-keys/plan-frozen.json) fixes the three source branches, keys, clocks and controls. [Per-setting results](experiments/records/dukotah-fixed-numeric-keys/results.json) preserve scores and complete decoded-output hashes. From a Liberpedia checkout, run:

```text
python experiments/records/dukotah-fixed-numeric-keys/run.py --check
python experiments/records/dukotah-fixed-numeric-keys/check.py
```

The first command runs the [pinned B1](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/b1_mayan.py), [B4](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/b4_hash_kdf.py) and [C2](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u/liber-primus/analysis/campaign7/c2_cuneiform.py) scripts in a temporary copy and compares each result with its archived JSON. The second reconstructs the operations and controls without importing those programs. Their exact source and inputs are bundled under the source project’s MIT license. The original results were already available when this local plan was frozen; this is a **replay and audit**, not a previously blinded search.
