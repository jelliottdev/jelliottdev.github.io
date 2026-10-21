# Complete historical prefix symbol inventory

This input audit extends the twelve-file convenience sample to every `files/` path in the pinned Project Runeberg source revision `a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87`. Its purpose is to measure the scope of the symbol-inventory difference without inventing the missing converter.

## Declared scope

- Verify the complete Git tree against the existing source inventory (25,906 paths).
- Read committed bytes offline, check Git blob identity, decode UTF-8 strictly, and preserve a SHA-256 per blob.
- Use the historical literal-space token rule, discard empty slots, and select at most the first 2,902 nonempty tokens. Newlines and other non-space characters remain counted units.
- Inventory every selected code point, then compare with the stored 29-rune manuscript alphabet. Do not drop, normalize or relabel characters.
- Keep shorter files separate from eligible prefixes. Report both path-weighted and distinct-blob-weighted totals and per-character prevalence.
- Preserve per-file counts and per-blob checkpoints. An interrupted run is not a completed census, and cached measurements need an independent source check before publication.

This is a descriptive audit, with no significance threshold or language-ranking claim. It does not inspect all characters beyond the selected prefix. A one-for-one symbol relabeling preserves token lengths; deletion changes them. Neither operation is licensed by an unknown conversion convention.

## Execution and review

With Python 3, Git and all pinned source objects already present, run the full offline pipeline from the Liberpedia repository root:

```sh
python scripts/run_corpus_symbol_audit.py SOURCE_REPOSITORY --output NEW_OUTPUT_DIRECTORY
```

This wrapper stops at the first failed stage. It refuses an existing output directory so a new run cannot overwrite evidence. For a deliberately interrupted measurement, the individual measurement command below can resume under its unchanged specification; verification and export must still follow. The earlier census report used for reconciliation remains a required local input under `experiments/records/corpus-prefix-census/report.json`.

```sh
python scripts/test_corpus_symbol_inventory.py
python scripts/corpus_symbol_inventory.py SOURCE_REPOSITORY --output NEW_OUTPUT_DIRECTORY
python scripts/check_corpus_symbol_inventory.py SOURCE_REPOSITORY NEW_OUTPUT_DIRECTORY/report.json --receipt NEW_RECEIPT.json
python scripts/export_corpus_symbols.py NEW_OUTPUT_DIRECTORY/report.json NEW_RECEIPT.json --output NEW_TABLE_DIRECTORY
```

The runner disables Git lazy fetching and never executes source-repository code. A missing source object stops the run. Existing checkpoints may resume only under an identical specification and script hash; a completed report cannot be overwritten.

The initial run was deliberately stopped after preserving 8,091 distinct-blob checkpoints to replace one Git process per blob with a persistent batch reader. This changes transport overhead, not tokenization or measurement. The replacement run uses a new output directory and specification hash; it does not silently reuse checkpoints from a changed script. All 8,091 original completed checkpoint objects were compared with the replacement measurements and agree exactly as parsed JSON, including source hashes and every symbol count. The original partial directory is retained. This transport comparison does not replace the independent complete-source audit, and neither partial directory constitutes a completed census.

Boundary controls cover leading/repeated spaces, newline retention, exactly 2,902 selected tokens, an outside-alphabet symbol immediately after the prefix, empty input and invalid UTF-8. The two scanners also agree on all 1,365 strings of length zero through five over a four-character alphabet containing an ordinary rune, the outside-alphabet rune, space and newline.

The independent checker imports no producer code. It uses literal-space splitting and scalar dictionaries, reads pinned blobs through a single offline Git batch process, checks duplicate rows, and reconstructs all four summary populations. It also reconciles each source hash, byte count and eligibility flag with the completed historical census, and every eligible prefix's exact word-length histogram and total counted units. A receipt is written only after every source row and aggregate passes. It has not yet run on the complete new report.

Publication remains pending: verify all measurements against an independent source scanner, reconcile hashes and eligibility with the existing census, then update the word-length guide and its downloads. No corpus-wide symbol result has yet been accepted from this run.

## Reader-facing tables

The export stage requires a complete report whose hash matches the independent receipt, with the full path and distinct-blob counts. It preserves separate CSVs for all per-file measurements, outside-alphabet characters, and the four populations. The character table distinguishes entry prevalence from occurrence counts and includes Unicode code points and names. The population table keeps zero cases visible; it prevents shorter texts from silently becoming part of the eligible-prefix denominator. Unicode naming database version is recorded in the accompanying text file. Export rejection and denominator-formatting controls are in `scripts/test_export_corpus_symbols.py`.

The generated `coverage.svg` uses one 0–100% scale for each of the four populations and prints the exact affected-entry count and denominator. It counts an entry once even if that entry contains many outside-alphabet symbols. Empty populations receive an explicit label rather than a zero-percent result. The figure still requires rendered review with the verified corpus data before publication.
