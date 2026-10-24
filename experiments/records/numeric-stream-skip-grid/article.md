# Numeric keys with conditional skips

**None of the 322 complete-page outputs selected by this numeric-key search cleared its English-score bar.** We ran the source's 33-stream catalog over the 55 rune-bearing pages in LP2-00–55, allowing key positions to be skipped under its repeated-rune rule. The search first checked 50 runes at each of **36,300 settings**. Only the 322 short outputs above −6.5 received a complete-page decode. Their strongest score was **−6.412 on [LP2-49](#/reader/lp2-49)**, below the source's −5.5 confirmation bar.

![36,300 short screens selected 322 complete-page checks. None cleared the source score bar; the strongest complete output on LP2-49 scored −6.412. Higher scores mean more English four-letter patterns, not proof of plaintext.](experiments/records/numeric-stream-skip-grid/numeric-skip.svg)

## The rule being tested

Normally, one key value serves each ciphertext rune. Here, the decoder may bypass up to three key values before accepting the next one—but only when **each bypassed value would have produced the preceding ciphertext rune again**. It explores possible paths and retains the paths with the best cumulative English four-letter score. This is a specific hypothesis about avoiding repeated output runes; the manuscript's lack of repeats does not establish that it used this rule.

The 33 labelled streams comprise five number-theoretic sequences; two decimal encodings each of π, e, φ, √2 and ln2; and three historical generator constructions with six fixed seeds. Each stream contains exactly **1,176 values**. Every page starts separately; both arithmetic signs, Atbash off/on and key offsets 0–4 are tested. The source's 841 Fibonacci seed pairs are excluded.

The original source beam remains unchanged: width 60 for the first 50 runes, strict short score greater than −6.5, then width 200 on the complete page for survivors, with strict confirmation score greater than −5.5. The best short score was −5.914 on [LP2-12](#/reader/lp2-12), using the e-digit stream, addition, Atbash and offset three. Its short-score success did not produce a full-page confirmation. The best complete output used φ digits, subtraction, Atbash and offset one on the 66-rune LP2-49 page.

## What the controls establish

Before manuscript execution, we tested two complete known readings across both this catalog and the related 21-stream artifact catalog. The preserved receipt contains **all 1,080 labelled control cells**: 540 sign/key/offset/reading cases, each represented with and without Atbash. The Atbash pair has the same underlying decoding problem, and periodic key phases add aliases, so these are not independent trials. Of the plants, **1,036 actually contain skipped keys** and 44 contain none. Seeds were selected by the frozen rule solely to keep every planted step within the decoder's maximum of three skips; none was omitted.

Every plant passed both source score gates, but only **1,036 of 1,080 returned the exact entire reading**. This catalog's subset recovered **634 of 660** exactly; the artifact subset recovered 402 of 420. In all 44 mismatches, the true planted path was valid and the chosen alternative had a strictly higher cumulative score—there were no ties. Passing an English-score gate therefore does not establish exact plaintext recovery. A different, fixed wrong key passed both gates in **0 of 1,080** cells; those controls do not calibrate the maximum of the full manuscript search.

## Boundaries and checks

The five decimal-constant families are the **source's finite constructions**. In particular, its e calculation is a 299-term approximation that diverges from high-precision e at digit 612, counting the integer digit. We preserve its exact generated digits rather than silently replacing them. The BBS-labelled generator also preserves source seeds 503 and 311 even though they are not coprime to its modulus; these are historical labelled constructions, not claims of standard generator quality.

Earlier records overlap some numeric ideas but use different clocks or acceptance rules: [fixed numeric keys](#/experiments/dukotah-fixed-numeric-keys), [opening-crib seed tests](#/experiments/typed-seed-random-opening-cribs), and [ciphertext-feedback coefficients](#/experiments/dukotah-ciphertext-feedback-coefficients). The last imports the numeric module as a helper without running this catalog. This record reproduces the source's explicit no-Fibonacci branch; it does not independently reproduce its larger historical full-catalog campaign.

All 55 source page arrays match the site transcription. The source run took **33.11 seconds**. An independent Latin-string scorer checked every one of the 36,622 stored outputs, and a separate scalar beam reconstructed every full survivor plus the maximum short output. The [frozen plan](experiments/records/numeric-stream-skip-grid/frozen-plan.json), [results](experiments/records/numeric-stream-skip-grid/results.json) and complete output ledger preserve the grid and outcomes. Source/model/input bytes and the full control receipt are bundled under the source project's MIT license.

**Separate post-target audit.** The source ranks paths by cumulative score but applies its reading gate to the normalized score. We therefore inspected all **56,273 retained terminal candidates** across the 322 full searches without changing the historical source-selected outputs. Normalized ranking chooses a different path in 284 cases. None of those candidates clears −5.5 either; the best normalized candidate scores **−6.372** at the same φ-digit/LP2-49 setting. The [audit](experiments/records/numeric-stream-skip-grid/terminal-audit.json) preserves its own plan, every best-normalized path and the empty above-bar witness list. This audit is a diagnostic added after the original target run, not a second solving method or an expanded beam search. The figure reports the original source-selected maximum.

The rejected short screens were **not decoded as complete pages**. No full-search shuffled reference was run, so the maximum has no search-adjusted significance claim. These results concern the listed keys, five phases, source pruning and English scorer; they do not exclude other numeric keys, skipped-key models, languages or encryption families, and do not establish an OTP explanation.

From the checkout or an isolated experiment bundle, with Python 3 and NumPy:

```text
python experiments/records/numeric-stream-skip-grid/run.py --check
python experiments/records/numeric-stream-skip-grid/check.py
python experiments/records/numeric-stream-skip-grid/terminal_audit.py
python experiments/records/numeric-stream-skip-grid/plot.py --check
```

The replay compares all deterministic output bytes and numerical fields without changing expected results. Timing is recorded separately. The independent checker imports no source decoding or scoring functions.

The complete frozen 1,080-cell known-message controls can also be replayed offline from this extracted bundle, without a source cache. The [portable control adapter](scripts/replay_numeric_skip_controls.py) checks the original probe and used-source hashes, preserves the frozen files, and compares every skip, decoded hash, gate and exact-recovery flag; only timings are ignored, with a 2e-12 score tolerance. Run:

```text
python scripts/replay_numeric_skip_controls.py --record experiments/records/numeric-stream-skip-grid
```
