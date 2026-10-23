# Feedback experiment engine

`feedback.py` implements two reversible rune-index ciphers on the canonical 29-symbol alphabet. For rune position `i`, `P[i] = C[i] − K[i] (mod 29)`. Before the chosen lag is available, `K[i]` is one scalar primer. Afterward it is either `C[i−lag]` (ciphertext feedback) or the already decoded `P[i−lag]` (plaintext feedback). State resets at each page. A manifest can request one continuous page stream or a reset after each literal hyphen/period; slashes and newlines are layout, not resets.

`feedback_suite.py` runs a declared cross-product of modes, lags, primers and boundaries. It takes a JSON manifest with `schema: liberpedia-feedback-suite-manifest-v1`, `engine: gp29-feedback-v1`, a unique `suite_id`, `alphabet_path`, ordered `pages`, `page_path_template` containing `{page}`, ordered `modes`, `lags`, `primers`, `boundaries`, `declared_config_count`, and `cribs`. Each crib has an ID, a nonempty index vector in 0–28, and a source file path and SHA-256. An optional `crib_source_plan` pins an existing `plan.json` whose `openings` must equal the manifest cribs. The pilot manifest uses that to verify nine original known-reading CSVs.

Import `build(manifest_path)` to get `(summary, cases)`. The suite wrapper accepts `--manifest PATH`, `--output-dir PATH`, and exactly one of `--write` or `--check`:

```sh
python experiments/suites/feedback-opening-census/run.py --check
python experiments/suites/feedback-opening-census/run.py --manifest experiments/suites/feedback-opening-census/manifest.json --output-dir experiments/suites/feedback-opening-census --check
```

The deterministic `cases.json` stores every configuration's full-decoding SHA-256, exact opening matches, maximum prefix length and ties. The digest is over lines `page<TAB>comma-separated-decimal-indices<LF>` in manifest page order. `results.json` stores all input hashes, the cases-file hash, counts and the maximum-prefix distribution. The runner tests an encrypted synthetic fixture for every configuration. It does not score language, search later positions or claim that a no-match result excludes other cipher models.

Performance note (Windows checkout, 22 October 2026): a file-per-case cache prototype took 14.9 seconds on a warm 1,856-case run, versus 7.1 seconds uncached. The cache was removed; the figures are one local measurement, not a general benchmark.
