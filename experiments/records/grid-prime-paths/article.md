# Directional prime paths: a reproduced count claim

This record checks a specific observation about the alphanumeric grids on LP2-49–51. It reproduces **191 occurrences of 46 distinct decimal primes**, with **1033, 2213 and 3301 absent** from a 49-value candidate set. “Supported” refers only to that scoped recount. It does not establish deliberate construction, statistical significance or a hidden message.

The [illustrated grid guide](#/wiki/alphanumeric-grids) identifies the original pages and their token conventions. The [prime-path guide](#/wiki/grid-prime-paths) explains the reconstruction and comparison with the published occurrence CSV. This experiment packages the inputs, complete output and two independent implementations for reuse.

## Fixed search rules

Stack the 32 original rows in page order 49, 50, 51, retaining eight columns. Read four consecutive cells in each of eight straight directions. Paths cannot turn or wrap around an edge, but may cross page boundaries. Reverse directions count separately.

Take the first character of each token. Reject any path containing a 4; do not remove the cell and join its neighbors. Interpret the four-position string as a decimal integer, allowing leading zeroes, and retain it if prime. Then record the four suffix characters and, separately, the base-4 interpretation of the digit string.

For example, LP2-49 grid coordinates (row, column) `(7,2) → (6,3) → (5,4) → (4,5)` contain `0G → 0S → 0d → 2U`. The digit string is `0002`, the decimal value is 2, and the suffix extraction is `GSdU`. Retaining the path does not make those suffixes plaintext.

## Complete result

There are 1,364 geometrically valid directed paths. Of these, 306 contain a 4 and are rejected, leaving 1,058 eligible paths. The decimal-prime filter retains 191 occurrences, including 60 with leading zeroes and 40 crossing a page boundary. These counts describe overlapping paths, not independent trials.

There are 256 possible four-position strings over digits 0–3. Their decimal values include 49 primes; 46 occur in the grid. The three missing strings become 79, 167 and 241 respectively when read in base 4. All three conversions are prime, but that is a separate observation: the original filter tests decimal primality. Only 147 of the 191 retained occurrences are prime under both interpretations.

The JSON contains every retained path, its tokens, original page coordinates, direction vector, digit string, suffix extraction and both numerical interpretations. Its frequency table includes all 49 candidate primes, including zero counts. No appealing suffix string was selected as a successful decryption.

## Reproduce

Extract this experiment’s ZIP with its directory structure intact. Python 3.12 and the standard library are sufficient; no installation, network call, AI service or key is needed.

```text
python experiments/records/grid-prime-paths/run.py --check
python experiments/records/grid-prime-paths/check.py
```

The producer uses the shared, included `grid_prime_paths.py` helper to enumerate starts and direction vectors from the coordinate-bearing export. Without `--check`, it prints a fresh JSON report.

The independent checker reads the original archived page records, reconstructs their grid tokens, and enumerates pairs of endpoints instead. It uses a sieve to identify primes rather than the producer’s trial division. It checks the complete set of hits, source coordinates, suffixes, base-4 values and frequency table. Agreement checks the implementations against the same archived transcription; it is not an independent visual reading of every glyph.

## Limits and related variants

Changing to a 16×16 layout, prohibiting page crossings, requiring four nonzero-leading decimal digits, searching longer paths, or requiring both bases to be prime changes the test. Keep such experiments in this family with their changed rules and results visible.

A linked [shuffle-control experiment](#/experiments/grid-prime-path-null) now fixes the path rule and compares the *number* of absent prime values with global and within-row first-digit shuffles. Three or more values were absent in about 15% of each control set. This does not assign a confirmatory probability to the particular three names selected after observation. Shuffling entire tokens would preserve different relationships from shuffling only first characters, and this baseline still does not claim that other representations were exhaustively excluded.

Read [search space and bounds](#/wiki/search-space) and [null models and selection](#/wiki/null-models) before turning this reproduced pattern into a claim about intention.
