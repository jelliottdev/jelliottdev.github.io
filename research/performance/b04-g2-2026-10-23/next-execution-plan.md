# B04 manuscript sweep: held for review

The fresh `control.py` G2 replay searched all 1,385,600 planted-control settings. The planted configuration ranked first at −4.157193769763151; G1 and G2 both passed. `gate-receipt.json`, `manifest.json`, and `independent-check.json` are copied byte-for-byte from the external checkpoint archive at `C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/b04-g2-control-20261023/`. The 542 chunk files and complete merge remain there (about 53 MB of chunks); keep that archive rather than copying it into the site.

The proposed target is the pinned source revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`, using the source decoder and scorer without changing its key-extension behavior. The runner refuses the target without `--allow-full` and a G1/G2 receipt matching source hashes, the ordered seed dictionary, and the G2 plant ciphertext. Each target-stage manifest freezes the actual segment bytes, complete candidate axes, seed order, source/data hashes, and chunk size before any decoder work. Finished chunks are atomic, checked, and reused after interruption.

## Exact targets and cost

| Stage | Target and complete grid | Decodes | Planned chunk |
|---|---|---:|---:|
| A | First 120 source unsolved runes; 2,165 seeds × 16 generators × 5 reductions × 2 signs × 2 Atbash settings × 2 directions; offset 0 | 1,385,600 | 4 seeds |
| B | Same 120 runes; 504 core seeds × 16 generators × 2 reductions × 2 signs × 2 Atbash settings × 2 directions × offsets 1, 4, 16, 29, 64, 128, 256, 512, 1024, 3301 | 1,290,240 | 4 seeds |
| C | First up-to-100 runes of each of 55 nonempty source pages; 504 core seeds × 16 generators × 2 reductions × 2 signs × 2 Atbash settings; forward, offset 0 | 3,548,160 | 1 seed |

Total A/B/C: **6,224,000 candidate decodes**, not 6,224,000 separate ideas. The source's saved A/B/C times total 3,438 seconds (about 57 minutes), but do not predict this host precisely. The fresh four-worker G2 took 1,331 seconds for its main resumed invocation plus the four-chunk pilot. At four workers, reserve roughly **one to two hours** for A/B/C, then revise from completed chunk rates. Run one stage at a time to leave capacity for site and other research work. A/B/C may be paused and resumed without changing its output directory or settings. Do not shorten a grid after seeing scores.

Stage D is a separate decision after all three complete: the source combines each stage's top 50, sorts by score, deduplicates exact configuration tuples, then deepens at most 150 distinct tuples on both source page 0 and the joined unsolved stream. The saved source Stage D has **150 page decodes** (6.3 seconds) and **150 full-stream decodes** (10,192.1 seconds, about 2 hours 50 minutes) on its original host. That is **300 Stage-D decodes total**. Stage D has no checkpoint wrapper yet. Require a reviewed exact tuple list and its own resumable plan before it starts.

## Source page alignment

`check_page_alignment.py` rebuilt GP-index streams from every site LP2-00–55 `raw` transcription and compared them with all 55 nonempty source segments. All 12,956 rune indices match in joined order. Source `page00`–`page49` align with site LP2-00–49; source `page50`–`page54` align with site LP2-51–55. Site LP2-50 has a grid but zero rune transcription and is skipped by source `load_pages()`. This mapping is checked per page and pinned in `page-alignment.json`. A/B's 120-rune head begins at site LP2-00. C includes site LP2-55 and excludes rune-empty LP2-50.

## Commands after approval

From `work/research-wiki`, with the pinned source checkout at `C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301`:

```powershell
$src = 'C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301'
$gate = 'research/performance/b04-g2-2026-10-23/gate-receipt.json'
$runner = 'research/performance/b04-2026-10-23/resumable.py'
python $runner --source-root $src --stage A --output ../b04-lp2-A-20261023 --nproc 4 --chunk-seeds 4 --topk 300 --gate-receipt $gate --allow-full
python $runner --source-root $src --stage B --output ../b04-lp2-B-20261023 --nproc 4 --chunk-seeds 4 --topk 300 --gate-receipt $gate --allow-full
python $runner --source-root $src --stage C --output ../b04-lp2-C-20261023 --nproc 4 --chunk-seeds 1 --topk 300 --gate-receipt $gate --allow-full
```

Those commands are **planned, not executed**. Before launching A, verify the three copied G2 artifacts against the external originals and rerun the page-alignment check. After each stage, independently verify all chunk hashes, decode counts, histogram sum, and source summary. Do not describe a score below −5.5 as a general failure to solve LP2; the test covers this finite seed/generator/decoder/scorer grid, and any negative interpretation depends on the applicable controls.

The source `Pool.imap_unordered` and score-only top-K heap rule leave cutoff ties dependent on completion order. The checkpoint wrapper writes chunks as completed but merges them in seed order, making the run reproducible; exact tied row identity may differ from an archived source run. Such a tie could affect Stage-D tuple selection. The source beam also zero-extends a key when it predicts insufficient remaining symbols; that behavior is preserved and must be audited for selected paths before a broad conclusion.
