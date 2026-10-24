# C-01 held-corpus replay — private review draft

The unchanged source scan found no complete word-length skeleton match in the tested held-text alignments. This is a bounded replay of the currently held files, not a replay of the historical 224-text corpus and not a plaintext or language exclusion.

## Exact scope

The loader selected 94 files containing 9,808,699 normalized words. The unchanged scanner admits 84 files containing 9,799,472 words: it omits 10 files shorter than 2,928 words, even for its shorter patterns. `independent-target-audit.json` lists every omitted file. The corpus files occupy 57,587,613 raw bytes; none is copied into this folder.

The target is the source parser’s first 55 percent-separated segments, producing 2,928 word lengths and F counts. It splits on dash/period and treats slash as a line wrap. T1 uses exact, symmetric slack-one and directional-F-interval matchers; four full-pattern permutations; the first 400 and 120 word prefixes with two permutations each. It does not scan all manuscript subwindows.

| Window | Unique eligible alignments per pattern | Source evaluations including block overlap |
|---|---:|---:|
| 2928 | 9,553,604 | 9,553,604 |
| 400 | 9,765,956 | 9,874,660 |
| 120 | 9,789,476 | 9,910,220 |

## Results

| Real pattern | Integer maximum | Text | Word offset (zero based) | Shuffled maxima |
|---|---:|---|---:|---|
| real:exact | 593/2928 | keys/tyndale_new_testament.txt | 145429 | 586, 590, 583, 588 |
| real:slack1 | 1445/2928 | keys/tyndale_new_testament.txt | 144747 | 1450, 1445, 1448, 1448 |
| real:interval | 664/2928 | keys/tyndale_new_testament.txt | 145429 | 656, 662, 650, 659 |
| realW400:interval | 109/400 | data/kjv.txt | 192907 | 109, 109 |
| realW120:interval | 47/120 | keys/homer_iliad.txt | 26860 | 48, 50 |

Counts measure compatible word-length positions; they are not decoded words. All 21 saved global witnesses were independently recounted by direct integer comparisons. Stored per-text maxima have membership, bound and near-integer checks, not an independent exhaustive rescan. Original floating maxima and tie choices remain unchanged. The small shuffled sets do not support a calibrated global probability or a claim of equivalence. The source stdout retains its descriptive z calculations; no inferential conclusion here uses them.

## Controls and freezing

Before targets, nine synthetic cases across 120/400/2928 word windows passed 103,995 independent offset counts for all three matchers, including block joins and tail plants. A synthetic production-size block took 0.259 seconds for three patterns. Source T0 then recovered KJV @134137 and Emerson @57592 at their exact planted locations: exact 2506/2928 and interval 2928/2928 for each. Source selection supplies only these two eligible plant texts in the held corpus, plus one shuffled pattern (exact 688; interval 772). No replacement plant or corpus expansion was added.

The source’s T0 preregistration discusses a null z gate and degradation floor. One shuffled T0 pattern does not establish that gate; T0b/T0c were not run. The demonstrated control is exact planted-location recovery.

`inputs-frozen.json` pins every raw and normalized corpus input, manuscript input, source dependency and earlier control receipt. Controls were frozen first, then executed, then `target-plan-frozen.json` was written before T1. The original preflight runner bytes are retained in `replay-controls-frozen.py`; its initial expected count of six planted matcher cases was corrected to the actual four in the current wrapper before target freezing. No source scanner/selection code changed. The sole source runtime adaptation redirects output HERE to this private folder and fixes argv to T0/no extra globs.

Executed commands from this folder (source/cache layout expected by `replay.py`; outputs are intentionally overwrite-protected):

```text
python replay.py freeze-controls
python replay.py controls
python replay.py t0
python replay.py freeze-target
python replay.py target
python replay.py audit
python check_t0.py
python check_public_provenance.py
python assess_arrays.py
python summarize.py
python check_receipt.py
```

T0 runtime including source loading: 40.79s; T1 runtime including source loading: 94.95s. NumPy 2.5.4 / Python 3.12.10. Reproducing requires a fresh output directory; do not overwrite these frozen receipts.

## Reproduction without corpus redistribution

Source: https://github.com/Dukotah/cicada3301 at f08b20b632d91209ddbaa747e8e2f23df0c78ba1. All 93 non-KJV held files match exact public Git blobs at that revision. KJV is gitignored: use a local file matching SHA-256 `0f1a83cbcdc1d3fae6bcc3daaa496d4fa723fcce9526e84e20df12ae33fda986` (4,436,268 bytes). The earlier exact download receipt records https://www.gutenberg.org/files/10/10-0.txt; an already-published matching local alternative is `experiments/records/dukotah-offset-model-integrity/source-kjv.txt`. This replay made no network request and does not promise that today’s download is unchanged. Stop on any raw/normalized hash or loader-membership mismatch; do not substitute editions.

The source code has an MIT license (2026 Dukotah), verified against the pinned Git tree. Individual corpus redistribution rights are not resolved by that license or public availability. A minimal future reproduction bundle can contain the authored scripts, plans/hashes, outputs/audits, four exact L4 source modules, gematria.py, manuscript input and original MIT license; require the 94 text files as external hash-validated local inputs. No full corpus redistribution is needed. `publication-assessment.json` records the evidence and limits.

A derived-array bundle is also feasible in principle: all 94 exact normalized int16 arrays total 19,617,398 bytes, or 4,727,489 bytes with each array deflated separately. Keeping the ten short arrays preserves the source's 94-entry totals and costs little. Every normalized array hash was rechecked against the pre-target manifest. A future adapter could return those identical arrays to the unchanged scanner, but must validate names, order, metadata and hashes and pass independent loader/fixture parity checks. That would reuse recorded normalization, not independently rerun it. This assessment saved no arrays and makes no legal redistribution claim. The current manifests, scripts and receipts plus the five source modules, manuscript and MIT license would be roughly 0.35 MB before any derived arrays; a self-contained array option would add roughly 4.73 MB compressed, excluding container overhead.

## Proposed reconciliation

`proposed-reconciliation.json` proposes keeping C-01 partial while marking this bounded held-input replay complete. Historical 224-text coverage, short-text prefix correction, alternate editions/conventions and degradation-floor bounds remain outside this replay. No public record, registry/catalog edit, build, commit, corpus expansion or threshold tuning was performed.
