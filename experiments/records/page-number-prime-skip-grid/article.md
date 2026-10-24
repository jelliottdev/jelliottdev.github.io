These page-number keys did not produce a reading that passed the fixed English-score test. Seven complete-page outputs were selected from 660 short trials; all failed the source's final score gate. A separate audit of every retained final candidate also found no gate crossing. This is a bounded conditional-skip extension of known linear ramps, not evidence that page numbers have no possible use.

## What was tried

The pinned source assigns each nonempty page index i three repeating arithmetic streams. Key position j starts at zero, and all values are reduced modulo 29.

| Source rule | Value at key position j |
| --- | --- |
| prime | prime[i mod 29] + j, using the 29 primes through 109 |
| [totient](#/wiki/totient) | phi(i+2) + j |
| 3301xor | 24j + i; the source label does not perform XOR |

The source index runs 0 through 54 over nonempty pages. Its index 50 therefore means LP2-51, not the blank LP2-50. Each key is used only on its assigned page, with both signs and ciphertext [Atbash](#/wiki/atbash), offset zero. That gives 660 settings. The 165 page-assigned labels contain 56 base arrays, or 112 distinct signed arrays. Repeated arrays assigned to different pages still require their respective page tests.

The source first decodes 50 runes with beam width 60. Only normalized scores strictly above -6.5 receive a complete-page decode with width 300; the final gate is strictly above -5.5. F behaves like every other rune. Headings remain, and state resets on each page. The source PartC function executes unchanged under return-preserving observers; its returned hit list and best short score agree with the recorded cases. Parts A/B are excluded.

## What a conditional skip adds

Without skips, the 330 Atbash-off settings are already inside the [whole-page progressive Caesar test](#/experiments/wholepage-progressive-caesar), P=C+k*i+b. That record does not establish coverage of the 330 Atbash-on rigid forms P=28-C+k*i+b. This replay keeps that orientation distinction explicit while treating the work as an extension of known ramp rules, not a new broad key family or a test of page-number significance.

Here every signed key step D is nonzero: 1, 24, 28 or 5. The source permits up to three rejected keys in general, but two consecutive rejections would require equal consecutive ramp values, which is impossible. A single rejected key is admissible exactly when the previous transformed ciphertext index minus the current index equals D modulo 29. The independent decoder uses this simpler rule rather than the source's generic rejection loop. It reproduces every short output, complete-page output and ordered final beam.

The figure shows an actual selected path on LP2-39. At zero-based rune position 105, transformed ciphertext indices 19 then 20 give (19-20) mod 29=28, matching the signed key step. The key pointer advances from 104 to 106. This is an admissible candidate path, not a certified plaintext or an inferred real skip.

## Controls and limits

A control plan was frozen before manuscript calls. All 112 distinct signed arrays received one fixed known reading, alternating the existing 184-rune Warning and 85-rune LP2-56 readings. The source encoder used suppression 0.83 and seed 3301, with no resampling. Every plant contains a genuine skip; none is omitted. All 112 pass both source gates, while 98 recover the complete reading exactly. Changing the ramp intercept only translates the planted ciphertext, so these are eight distinct step/reading situations rather than 112 independent power samples.

The 14 nonexact labels all repeat one situation: step 5 with Warning. The true reading remains second in the final beam in every case; the source selects a higher cumulative-score alternative. These are scorer preferences, not invalid plants, ties or pruning away the true reading. Gate passage therefore does not guarantee exact recovery.

The target plan binds the source, model, key rules, control receipts, site index and all 55 page texts before the new target calls. Source and site rune arrays agree exactly. Keys have 1,124 slots; the generic buffer requirement is at most 1,116, and the linear skip rule bounds the actual last consumed index at 552. An imported bigram prefilter is unused; direct beam calls use the bundled English quadgram table. The short/full source beam still ranks cumulative scores and gates normalized scores.

After the source outputs, a separately frozen POST-TARGET audit checks all 1,220 retained final hypotheses from the seven full decodes. Every setting has a better normalized alternative than the returned cumulative winner, but none crosses -5.5. Best returned complete score is -6.994514123971474; best normalized retained score is -6.944792840501962, both on the LP2-39 totient setting with subtraction and Atbash. This audit does not rerank intermediate beams or fully decode rejected screens.

Independent checks reconstruct all 660 short paths, all seven full paths and every ordered retained final hypothesis, verify the key formulas and page-index mapping, and separately reconstruct all 112 controls. A portable isolated replay repeats controls and the exact source target without a source-cache dependency. Scientific outputs agree byte-for-byte except timing fields. Original plans and outputs remain unchanged. The source is Dukotah/cicada3301 commit f08b20b632d91209ddbaa747e8e2f23df0c78ba1, with its MIT license bundled.

No plaintext is certified. These eight known-reading situations do not calibrate a maximum over the entire manuscript search, and no global probability, general numeric-key exclusion or OTP explanation follows. Other assigned rules, phases, clocks, languages and joined-page mechanisms remain outside scope.
