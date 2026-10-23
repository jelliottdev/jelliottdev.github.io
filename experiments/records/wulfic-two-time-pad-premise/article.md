# Do the proposed two-time-pad regions actually match?

Three [archived Wulfic scripts](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy) propose paired rune positions where a key could be reused. Their crib-dragging rules depend on those positions lining up. **The six claimed copies do not match the verified manuscript text.** Five point past the end of the scripts' own page stream. The one pair entirely inside that stream has only **7 equal runes in 404 aligned positions**, with a mismatch at the first position.

This checks the scripts' **specific claim of identical ciphertext spans**. Sharing an additive key does *not* require identical ciphertext: if the plaintexts differ, their ciphertexts normally differ too. Conversely, identical ciphertext alone would not prove that the keys match. The failed copy claim cannot support these crib placements, but it does not settle the general key-reuse question.

![Five proposed paired regions exceed the source stream; the in-bounds pair has 7 equal runes out of 404. A separate pairwise statistic is close to its shuffled-search median.](experiments/records/wulfic-two-time-pad-premise/alignment.svg)

The source calls its input files pages 21–54. We recovered **all 34 page files from the pinned source commit's Git objects**; their rune contents match the [verified input mapping](experiments/records/wulfic-keyword-prime-layer-grid/source-gp-hashes.json) to **LP2-04–37**, an **8,226-rune** stream. The files were merely omitted from the sparse local checkout. The proposed period of 6,726 would require positions through 13,451 for its first two blocks. Its subtraction loop cannot run on this input. The other script says its page 27 is a prefix of page 44. On the correctly mapped pages, those are LP2-10 and LP2-27: only **9 of the 234 available aligned runes** agree, beginning with a mismatch. Reading the labels instead as LP2-27 and LP2-44 still does not rescue the claim: **13 of 234** agree, again with a mismatch at the start.

One script also makes a separate, finite measurement: subtract or add every pair among those 34 pages, align at page starts, and screen the resulting rune frequencies. We replayed all **1,122** page-pair/operation cases and confirmed each score against the pinned script's own functions and committed page files. Five crossed its IoC screen of 1.15; the highest is **1.23** for LP2-12 against LP2-14 over **137 runes**. This is a selected frequency score, not readable plaintext. In a retrospective control that shuffles each page once per trial and repeats the whole pair search, **43 of 199** trials reached at least 1.23. The shuffled-search median was **1.19**.

The source screen has limited power at those lengths. When we encrypted ten fixed pairs of established LP1 readings with a deliberately shared key, only **two of ten** differences crossed 1.15. A score below that line therefore cannot rule out every reused key. The shuffles preserve each page's rune counts; they show how the *maximum of this search* behaves under that conditional comparison, not the chance that an arbitrary cipher is correct.

This result rejects the **specific claimed aligned-copy regions** as a basis for these crib placements. It does not exclude other two-time-pad or key-reuse models, which could use different ciphertexts and still share a key. We did not score cribs under a shared-key assumption whose named alignments fail the input check. The source script's running-key branches are separate proposals; [solved-text running keys](#/experiments/solved-reading-running-key) and [an Emerson running key](#/experiments/emerson-running-key) have their own bounded records.

The [plan](experiments/records/wulfic-two-time-pad-premise/plan.json) pins the three source files, exact page mapping, six paired spans, pairwise screen and controls. It is a **retrospective replay plan**: preliminary page results were inspected before the local plan was written, and the 199 shuffles are a diagnostic rather than a prospective discovery test. [Results](experiments/records/wulfic-two-time-pad-premise/results.json) retain every proposed region, the five threshold hits, all control maxima and all ten planted pairs.

To reproduce from a full Liberpedia checkout, run:

```text
python experiments/records/wulfic-two-time-pad-premise/run.py --check
python experiments/records/wulfic-two-time-pad-premise/check.py
python experiments/records/wulfic-two-time-pad-premise/plot.py --check
```

The independent checker reads the page JSON separately from the producer's text files. Pass `--source-root PATH_TO_WULFIC_CHECKOUT` to the checker to verify the three original script hashes, all 34 page Git objects and every page-pair score from the source functions at commit `bf89d3d13aad2b8f2c95ab195cf1b092f250775c`. A sparse checkout works if those Git objects are present.
