# Hint, scope and corpus cohort

Eight initial source reviews, one new bounded target measurement, and one new synthetic instrument-control grid. **No whole-method closure and no new public record.** The frozen source revision is `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`.

The most useful correction is C-01: the pinned source already contains the supposedly unperformed SKELETON extension. Round 10 L4 reports 224 texts / 22,643,594 words; this supersedes the original Round-8 51-text scope. That is archival evidence, not a new local target test.

Fresh exact-source L4 blocked FFT controls pass on nine synthetic corpora, crossing W=120/400/2928 with starts 0/2048/final. All nine directional-interval plants recover the full W-word count. A separately written direct matcher reproduces **69,330** exact/interval per-offset counts, including all blocked-search maxima. These controls validate that finite scanner implementation scope; the 224-text scan itself has not been rerun.

Fresh LENGTH measurements reproduce the source's 2,928 words, 12,956 runes, 458 F, and endpoint interval **[4.268443, 4.424863]**. Available eligible local text inputs are KJV and self_reliance; none of their **11,274 source-sampled passages** reaches either endpoint. This restricted comparison cannot reproduce the source's archived 44/47 statistic, nor show a global anomaly or its absence. The upper endpoint is explicitly tested here. Source code's long-text sampling and omission of the final valid window are preserved. The KJV bytes match the existing source-capsule pin; all other initial input files match committed git bytes.

The remaining entries have no newly executed target grid. F-02's map/road clauses lack concrete rules; B-06/B-07 name missing future evidence. B-15's trigram tensor remains expressly inconclusive. B-24's 85-rune specificity anchor remains underpowered. B-20's exact source scorer and ciphertext cache are absent, so its archived 2,670-read best is not treated as a fresh replay. No alternate model was substituted.

`proposed-reconciliation.json` provides all eight statuses and unresolved scopes. `selection.json` proves these were initially pending. `evidence-pins.json` verifies source documents and output bytes against the pinned revision. Existing public records such as the corpus-prefix census concern different statistics; they were not falsely linked as these method replays.

Reproduce from the repository root:

```text
python research/source-intake/hint-scope-cohort-2026-10-23/run.py
python research/source-intake/hint-scope-cohort-2026-10-23/check.py
python research/source-intake/hint-scope-cohort-2026-10-23/scanner-control.py
python research/source-intake/hint-scope-cohort-2026-10-23/check-scanner.py
python research/source-intake/hint-scope-cohort-2026-10-23/finalize.py
```

Local source cache is required; this internal intake receipt is not a standalone public experiment bundle. Both plans were frozen before their respective runs. Controls run before LENGTH target calls; the scanner control contains no LP2 target input. Archived source results were visible before planning, so these are replays/audits rather than blinded discoveries.
