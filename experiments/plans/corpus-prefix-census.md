# Full corpus-prefix census: execution preparation

This prepares a descriptive census, not a reproduced historical probability result. The machine-readable plan fixes the source revision, every eligible path, counting conventions and calculator hashes.

The calculator uses exact rational intermediate means and sample variances before serializing floats. Quantiles use linear interpolation. Five regression tests cover literal-space parsing and Unicode units, a hand-computed variance/quartile example, ties and duplicate weighting, the integer variance identity over 243 short sequences, and reconstruction of the pinned manuscript summary. Run:

```text
python scripts/test_corpus_prefix_statistics.py
```

Start the census with an existing pinned Git clone and a new output directory:

```text
python scripts/run_corpus_prefixes.py /path/to/project-runeberg --output /path/to/census
```

The default is offline. Missing objects stop the run and leave measurements in `blobs/`; a complete `report.json` is written only after all 25,906 paths are processed. Identical blobs are measured once but contribute a row for every path. Reuse the same output directory to resume; changed source code or conventions require a new directory. A directory with a completed report is not overwritten.

For a partial clone, `--allow-fetch` explicitly permits missing-object retrieval. The upstream repository's reported size is about 6.6 GiB; this is not an estimate of exact network transfer or final disk use. Check available storage before retrieving the full source. The runner does not execute corpus repository code.

The initial offline smoke run measured 70 cached objects and stopped on a missing object. It produced no complete report. That run used the initial runner before clearer stop messages were added; retain it as a smoke-run artifact, not a checkpoint for the current hashed specification.

Before publication, finish the census, independently check saved rows, retain the source hashes and eligibility ledger, and compare any claim with its exact reference population. In particular, do not silently substitute the 2,896 rune-only manuscript tokens for the historical 2,902-unit summary.

## Independent audit after completion

The separate checker reads the pinned source bytes through a single Git batch reader. It reconstructs prefixes with a regex scanner, checks exact histograms and duplicate rows, and uses Python's statistics module for sample variance and inclusive quantiles rather than calling the producer's calculator. Floating summary values use an explicit 1e-12 comparison tolerance.

```text
python scripts/check_corpus_prefixes.py /path/to/project-runeberg /path/to/census/report.json --receipt /path/to/new-audit-receipt.json
```

The receipt path must be new. No successful full-corpus audit is claimed until this command completes. The checker has passed the synthetic report checks below; its real full-corpus source-byte validation is pending the finished census.

The variance implementation uses the exact identity `(n * sum(x*x) - sum(x)**2) / (n * (n-1))` with integer sums and a rational final division. This replaces per-item rational subtraction without changing the statistical definition. The plan hashes were updated before the full census execution.

## Interruption and resume check

`python scripts/test_corpus_resume.py` uses a synthetic 25,906-path tree with three tiny source objects. It forces one source to be unavailable, verifies that no complete report appears, resumes from the saved measurement, and confirms that duplicated paths retain their full weight. It also checks that changed calculation code is refused and a completed report is not overwritten. The synthetic counts are test fixtures, not corpus measurements. This check passed before the full census was completed.

## Checker corruption controls

The same synthetic tree now exercises the independent checker against a completed 25,906-row fixture, backed by three source objects. Its Git batch-reader protocol is simulated in memory, so this is not an integration test of a live Git process. The checker accepts the intact fixture and rejects five deliberately damaged reports: a changed variance, changed histogram, inconsistent duplicate-object row, wrong eligible-entry total, and missing row. This checks report integrity and failure paths without downloading data. It does not replace the planned check of every real source blob.
