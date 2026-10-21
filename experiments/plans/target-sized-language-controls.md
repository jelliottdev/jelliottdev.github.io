# Exact target-sized language controls

## Question and prior knowledge

How reliably do the fixed FLORES development profiles distinguish the eight included languages when each evaluation sample contains exactly 2,896 tokens, the number in the existing unsolved rune-token target?

The full-document, aligned-block and known-reading experiments have already been inspected. English ranked nearest to the unsolved target in the earlier comparisons; some short known-English sections ranked nearest to other profiles. This is a follow-up control, not a blind language discovery. No new corpus, language, tokenizer or score is chosen using the results of this follow-up.

## Sampling rule fixed before scoring

Use all eight existing FLORES development and evaluation translations and the three common representations: letters, folded letters and GP-style grouping. Retain the baseline sentence-by-sentence tokenizer, so a token cannot cross a sentence boundary. Flatten evaluation tokens in original sentence order for each language and representation, and partition from offset zero into consecutive, disjoint blocks of exactly 2,896 tokens. Report every complete block. Retain the remainder's count and offsets in the report but do not score it as a target-sized sample. Do not wrap, pad, repeat or randomly resample the remainder.

Every included language receives the same rule. There is no Welsh-only representation or category in this control. Grouping changes token lengths, not token boundaries; verify that all three common representations have the same block token ranges within each language. Record the first and last sentence index for every block, including each endpoint's within-sentence token offset.

These blocks use the same translated corpus but do **not** preserve the same sentence ranges across languages. Different languages use different numbers of words for a passage. Equal token counts and identical translated passages are different design choices: this control addresses size, while the earlier aligned-block variant addresses matched content. Adjacent blocks can split a source article, so disjoint tokens do not imply independent samples.

## Fixed comparisons

For each block, calculate the word-length histogram with bins 1 through 15 and 16+. Compare it against all eight full development-language profiles in the same representation, using exact rational total-variation distance. Preserve all eight distances and all tied nearest candidates. A tie is neither silently broken nor counted as a unique correct decision.

Report per language and representation: number of complete blocks, number of unique correct decisions, number of unique wrong decisions, number of ties, the complete nearest-candidate tally, and each block's margin between its true-language distance and its nearest competing-language distance. Define the margin as nearest competing distance minus true-language distance; positive is a unique correct decision, zero is a tie involving the true language, and negative means a competitor is closer. Ties between competing languages are reported separately even if the true-language margin is negative.

Also compare the fixed manuscript histogram against the same eight development profiles, preserving all distances and ties. For each language and representation, report its manuscript-to-profile distance beside the minimum and maximum true-language block-to-profile distances. These ranges are descriptive; no p-value, probability, confidence interval or exclusion threshold is derived from them. The manuscript's genre, token units and cipher remain different from these reference texts.

Do not report a pooled accuracy that weights languages by their different block counts. Do not select the most flattering representation. Display all three representations and all eight languages, with identical styling for every language. Keep nearest-language ranking separate from whether any profile is a satisfactory absolute match.

## Verification and limits

The producer must verify every input hash. An independent checker must reconstruct tokenization, endpoint ranges, histograms, rational distances, ties and summary counts from the source translations without importing the producer or baseline tokenizer. Check that blocks do not overlap, no complete block is omitted, and the remainder completes the source token ledger.

This does not supply genre matching, language probabilities, all-language coverage, per-section unsolved classification or a decryption. Corpus profiles can contain more than 29 symbol types; the comparison is about token lengths under the stated representation, not a validated bijection to the rune alphabet. Human review remains pending after computational checks.
