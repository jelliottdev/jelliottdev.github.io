# Reproducing the historical corpus-prefix comparison

This directory contains the reproduction entry point. Results must pass the source-byte audit and the comparison audit before they can be published as a completed experiment. The frozen plans describe the calculation; their preparation-time status is not a live progress indicator.

## What you need

Use Python 3 and Git, with commands run from the Liberpedia repository root. The calculation uses the Python standard library. The source corpus is a separate Git repository and is not included in a Liberpedia reproduction bundle.

Retrieve the corpus without checking out its thousands of files:

```text
git clone --no-checkout https://github.com/mortlach/project-runeberg.git project-runeberg
git -C project-runeberg cat-file -t a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87
```

The second command must print `commit`. The runner reads objects at this exact revision, regardless of the current branch. It checks the complete tree against the saved inventory. A full clone transfers gigabytes; allow room for the Git objects and the generated measurement cache. No corpus-repository program is executed.

An existing clone is also suitable if it contains the pinned revision and every required blob. Avoid a shallow or filtered clone for the one-command offline run unless the missing objects have already been retrieved. Having the commit object alone does not establish that all source bytes are present.

## Complete run

Choose an output directory that does not exist:

```text
python experiments/records/corpus-prefix-census/run.py project-runeberg --output work/corpus-replay
```

This command stays offline and stops on the first failed stage. In order, it measures every source path, independently checks the source bytes and statistics, calculates all declared comparisons, independently checks the ranks and ties, and renders the complete comparison.

| Output | What it establishes |
| --- | --- |
| `specification.json` and `blobs/` | Calculation identity and resumable per-blob measurements; these can exist during an incomplete run |
| `report.json` | Every pinned path has a census row, including ineligible files; not independent verification by itself |
| `audit-receipt.json` | The independent checker reconstructed source measurements and checked duplicate rows against the original Git blobs |
| `comparison.json` | All 23 measures under both declared weighting rules |
| `comparison-receipt.json` | The independent comparison checker reconstructed all 46 rows, including exact ties and inclusive fractions |
| `presentation/comparison.svg` and `presentation/comparison.md` | A figure and exact-count tables generated only after the receipt chain passes validation |

Retain the measurement cache and both receipts alongside the reports. A comparison receipt checks the supplied census; it does not replace the source-byte audit. Rebuilding a figure alone is not a fresh reproduction of the measurements.

## If a run stops

Keep the existing output directory. The wrapper deliberately refuses to reuse it, so that it cannot accidentally replace evidence from an earlier run. To resume an interrupted census, use its lower-level command with the same source, code and directory:

```text
python scripts/run_corpus_prefixes.py project-runeberg --output work/corpus-replay
```

This reuses saved measurements only when the run specification agrees. A completed report is never overwritten. If a filtered clone lacks objects, this command can explicitly permit retrieval by adding `--allow-fetch`; the offline wrapper does not do this automatically.

After the census completes, run each remaining stage in order, proceeding only when the preceding command succeeds:

```text
python scripts/check_corpus_prefixes.py project-runeberg work/corpus-replay/report.json --receipt work/corpus-replay/audit-receipt.json
python scripts/compare_corpus_prefixes.py work/corpus-replay/report.json work/corpus-replay/audit-receipt.json --output work/corpus-replay/comparison.json
python scripts/check_corpus_comparison.py work/corpus-replay/report.json work/corpus-replay/audit-receipt.json work/corpus-replay/comparison.json --receipt work/corpus-replay/comparison-receipt.json
python scripts/render_corpus_comparison.py work/corpus-replay/report.json work/corpus-replay/audit-receipt.json work/corpus-replay/comparison.json work/corpus-replay/comparison-receipt.json --output work/corpus-replay/presentation
```

If a later stage already succeeded, preserve its output and resume at the first incomplete stage. Do not delete a failed check's evidence to make a rerun appear successful. Changed calculators or counting rules require a new run directory and a separately documented variant.

## What the comparison means

The reference is the first 2,902 nonempty literal-space tokens in every eligible file. Token length counts retained Unicode code points, without header removal or filtering to the rune alphabet. The manuscript target counts 2,896 rune tokens plus six isolated digits. This intentionally reconstructs the declared historical counting question; it does not make the units equivalent.

Path weighting retains repeated files. Distinct-blob weighting counts identical bytes once, but does not identify duplicate works, editions or translations. The converter and edition manifest remain unavailable.

Every measure is shown, including ties. The resulting fractions describe positions in this fixed corpus; they are not language probabilities or calibrated p-values. Neither an extreme rank nor a typical rank establishes a cipher or plaintext language.

See the [census plan](../../plans/corpus-prefix-census.md) and [comparison plan](../../plans/corpus-prefix-comparison.md) for the exact rules fixed before the full run.
