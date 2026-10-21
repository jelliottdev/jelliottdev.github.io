# Running the declared corpus comparison

The rules are frozen in `corpus-prefix-comparison.json` and its hashed Markdown account. This execution note does not amend those rules. The full source census and its audit are still pending; no corpus-wide comparison result is claimed.

After completing the census, first run its independent source-byte checker:

```text
python scripts/check_corpus_prefixes.py /path/to/project-runeberg /path/to/census/report.json --receipt /path/to/new-audit-receipt.json
python scripts/compare_corpus_prefixes.py /path/to/census/report.json /path/to/new-audit-receipt.json --output /path/to/new-comparison.json
```

The comparison verifies the plan's input hashes, the complete report's hash against the receipt, the receipt's checker hash, entry counts, token totals and duplicate statistics. A receipt is a reproducibility record, not a cryptographic signature: rerun the source audit rather than trusting an unknown receipt. The output path must be new.

Each weighting policy has all 23 measure rows. For every row, divide an inclusive numerator by `reference_count` to obtain its empirical fraction. The exact target comparison value is stored as a numerator and denominator. For `sample_std`, `comparison_scale` is explicitly `variance`: ordering and equality are calculated before taking square roots. Do not display that stored variance as a standard deviation.

Run the focused arithmetic controls with:

```text
python scripts/test_corpus_comparison.py
```

The four checks cover hand-calculated moments and interpolated quartiles, the 15+ bin, ties and duplicate weights, independent exact-statistics comparisons over 81 short sequences, and fractions too close for floating-point tie decisions. They passed on the development machine. They do not check real full-corpus results or replace the separate independent reconstruction required before publication. The comparison output retains that pending-review label.
