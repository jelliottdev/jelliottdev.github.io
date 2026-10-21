# Full corpus-prefix census: execution preparation

This prepares a descriptive census, not a reproduced historical probability result. The machine-readable plan fixes the source revision, every eligible path, counting conventions and calculator hashes.

The calculator uses exact rational intermediate means and sample variances before serializing floats. Quantiles use linear interpolation. Four regression tests cover literal-space parsing and Unicode units, a hand-computed variance/quartile example, ties and duplicate weighting, and reconstruction of the pinned manuscript summary. Run:

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
