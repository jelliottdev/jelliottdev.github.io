# Self-embedded reads and printed-line acrostics: source replay and limits

This audits two related entries in [Dukotah/cicada3301's ledger](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/LEDGER.json): `R22-A-SELFEMBEDDED-READ` and its printed-geometry follow-up `R23-A2-LINE-ACROSTIC`, at commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`. These are **source replays, not independent negative experiments**. Do not add them to Liberpedia's published experiment count as closed selection or acrostic searches.

## What ran

At the pinned revision, a sparse checkout of `liber-primus/analysis/round23/A2-line-acrostic`, `src`, `data` and `tests` ran under Python 3.12 on 22 October 2026:

| Command | Observed output |
| --- | --- |
| `python tests/validate.py` | Six reading validations passed. The source's historical report says five, because this revision's validator includes LP2-56. |
| `python PHASE0-GATE.py` | Two planted acrostics were recovered above their **own length-specific** bars; extractor check passed. |
| `python run_sweep.py` | 48 reads, 20 lengths, one length-cell crossing, zero crossings of the reported family bar. Best reported read: `06\|word_last\|rev`, score −6.223; family bar −3.597. |

The commands and output agree with the [source results](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round23/A2-line-acrostic/RESULTS.md). No input or threshold was changed for this replay.

The related [round-22 selection sweep](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/A-selfembedded-read/RESULTS.md) was also replayed at that revision. Its `PHASE0-GATE.py` recovered two planted messages at scores **−4.089** and **−4.073**, each above its own length bar. `run_sweep.py` tested **3,508 selection functions** (1,754 Latin-letter reads and 1,754 rune-index reads), found six length-cell crossings and **zero family crossings**, matching its report. The final family bars were **−2.562** for letter reads and **−2.711** for rune-index reads. Neither planted score crosses either final bar. This predecessor has the same decision-rule power gap as the printed-geometry follow-up.

## Scope corrections before adopting the conclusion

1. The source calls its inputs “five pages,” but its five `PAGES` entries are decoded **sections**. The [source transcription](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/data/scream314_lp.md) groups 06–09, 03–04 and 14–15. The tested text therefore spans ten LP1 manuscript images, rather than five individual images. The script concatenates those sections in `01, 05, 06–09, 03–04, 14–15` order; that is not manuscript order, despite the report's description.
2. The round-23 planted line-first and word-first controls score **−4.292** and **−4.021**. Both beat their own length bars (−4.797 and −6.257), but **neither beats the family bar of −3.597** required for a headline survivor. The round-22 plants likewise fall short of its family bars. These controls demonstrate extraction and sensitivity at the length-specific stage. They do **not** demonstrate power for either final decision rule. Consequently, zero family survivors cannot be called a control-validated absence of hidden messages of the planted strength.
3. The null shuffles the pooled decoded letters, then slices by read length. It does not keep line-start or word-start letter frequencies, word shapes, or the correlations among all 48 reads. The family bar is the largest null score across length cells, rather than a distribution of the largest of 48 full-search reads per trial. It may be conservative, but its calibrated family error rate and power are not established by the reported gate.
4. The source reports one length-cell crossing against `48 × 0.001 = 0.048` expected crossings. One is **above**, not below, that expectation. The reads are dependent, so the simple expected count is not a calibrated probability of this event. The crossing is gibberish and far below the source's family bar; it should not be treated as a solution.

Liberpedia's existing `text/lp1-*.txt` files and reading exports are not drop-in replacements for this source geometry. The archived LP1-01 text has nine rune-bearing rows while the source extractor uses ten; its source line-first string is `ABETFEDOEF`. The source has 742 runes in its 06–09 section and 394 in its 03–04 section, compared with 778 and 515 in Liberpedia's aligned reading exports. A new test must first reconcile the actual image rows, page breaks, rune scope and copied interrupters. An exploratory 88-read prototype using the archive's current line breaks was **not** published: its input geometry differs and neither planted control passed its final max-of-search threshold. Its null result therefore cannot count as a valid negative.

**Intake decision:** retain both related source results as reported, replayed attempts with these limits. The next publishable experiment needs image-checked geometry where line positions matter and a full-search control that repeats all selected reads. Positive controls must cross the same final threshold used to judge the manuscript.
