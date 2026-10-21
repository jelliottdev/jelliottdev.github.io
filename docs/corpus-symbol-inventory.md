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

```sh
python scripts/test_corpus_symbol_inventory.py
python scripts/corpus_symbol_inventory.py SOURCE_REPOSITORY --output NEW_OUTPUT_DIRECTORY
python scripts/check_corpus_symbol_inventory.py SOURCE_REPOSITORY NEW_OUTPUT_DIRECTORY/report.json --receipt NEW_RECEIPT.json
```

The runner disables Git lazy fetching and never executes source-repository code. A missing source object stops the run. Existing checkpoints may resume only under an identical specification and script hash; a completed report cannot be overwritten.

Boundary controls cover leading/repeated spaces, newline retention, exactly 2,902 selected tokens, an outside-alphabet symbol immediately after the prefix, empty input and invalid UTF-8. The two scanners also agree on all 1,365 strings of length zero through five over a four-character alphabet containing an ordinary rune, the outside-alphabet rune, space and newline.

The independent checker imports no producer code. It uses literal-space splitting and scalar dictionaries, reads pinned blobs through a single offline Git batch process, checks duplicate rows, and reconstructs all four summary populations. It also reconciles each source hash, byte count and eligibility flag with the completed historical census, and every eligible prefix's exact word-length histogram and total counted units. A receipt is written only after every source row and aggregate passes. It has not yet run on the complete new report.

Publication remains pending: verify all measurements against an independent source scanner, reconcile hashes and eligibility with the existing census, then update the word-length guide and its downloads. No corpus-wide symbol result has yet been accepted from this run.
