## The question this comparison asks

An earlier word-length analysis compared the unsolved manuscript with thousands of converted texts. Before interpreting a reported rarity, we need to know what was counted, which texts entered the comparison, and whether repeated files received repeated weight.

This experiment asks a specific descriptive question: **where does the reconstructed 2,902-token manuscript summary fall among the first 2,902 tokens of every eligible file in the pinned reference corpus?** It does not ask which language is most likely. The separate [parallel-language experiments](#/experiments/parallel-languages) compare aligned translations under declared representations.

**Publication status:** this account is prepared while the full source-byte audit is running. No final corpus finding is asserted here. A published record must include both successful audit receipts, all comparison rows, and the rendered figure.

## Why 2,902 rather than 2,896?

The [word-length guide](#/wiki/word-lengths?section=historical-count) reconstructs the historical summary by including six isolated digits alongside 2,896 rune tokens. Counting each digit as a length-one token reproduces the earlier summary. This does not make those digits runes, nor prove what the original author's parser intended.

The target for this experiment is that reconstructed historical summary. Switching to the rune-only target would change both the denominator and the reference-prefix length. It belongs in an explicitly declared variant, not an unnoticed correction during the calculation.

## What enters the reference population?

The pinned source tree contains 25,906 paths under `files/`. Every path is considered. A file is eligible when it has at least 2,902 nonempty tokens separated by the literal space character. Its first 2,902 tokens form its profile; later material is not sampled.

There is no language selection, header removal or filtering to the 29-rune alphabet. Strict UTF-8 decoding is required. Token length is the number of retained Unicode code points. A newline or another non-space character remains part of its token under this rule. This precision matters: a general whitespace splitter would implement a different experiment.

The [earlier twelve-prefix audit](#/wiki/word-lengths?section=corpus-inputs) found symbols outside the stored manuscript alphabet. The full census preserves the declared counting rule rather than silently deleting them. Relabeling a symbol one-for-one preserves length; deleting it can change lengths, empty tokens and subsequent prefix selection.

## Two ways to weight the same files

The primary comparison counts every eligible path. If two filenames contain identical bytes, both contribute. This preserves the historical file-based population.

The sensitivity comparison counts each distinct eligible Git blob once. This removes byte-identical duplication. It does not deduplicate editions, translations, differently formatted copies or separate excerpts from the same work. Consequently, neither population should be described as thousands of independent books.

Both versions show the same 23 measures: proportions of lengths 1 through 14 and 15+, mean, sample variance, sample standard deviation, minimum, lower quartile, median, upper quartile and maximum. The 15+ bin retains longer reference tokens even though the manuscript target has none. Measures are related; they are not 23 independent experiments.

## How to read the figure and exact tables

Each bar divides the reference population into values strictly below, equal to and strictly above the manuscript value. “Below” is a numerical relation, not a judgement of which text is more natural or more similar overall. For example, a prefix below the manuscript's length-two proportion simply contains a smaller proportion of length-two tokens.

The tables also retain two inclusive fractions: `(below + equal) / total` and `(above + equal) / total`. Ties enter both. With three reference values below the target, two equal and five above, the fractions are 5/10 and 7/10. They sum to more than one because both include the two ties. Subtracting either fraction from one would give the other *strict* side, not the other inclusive fraction.

Counts, means, variances and interpolated quartiles are compared using exact rational arithmetic. Standard deviation is ranked through variance, because taking a nonnegative square root preserves order and ties. Rounded values displayed to readers do not decide equality.

## What an extreme rank would establish

An extreme rank means that few of these particular file prefixes fall on one side of the manuscript under the specified counting rule. It is not a probability that the plaintext is English, a probability that the manuscript is natural language, or a calibrated hypothesis-test p-value.

The collection is fixed and nonrandom; its edition manifest and conversion procedure remain unavailable. File beginnings can contain material unlike the manuscript. Corpus units count all retained Unicode code points, while the target counts runes plus six digits. These limitations remain even if the arithmetic is reproduced exactly.

For a one-symbol-for-one-symbol cipher with preserved boundaries, plaintext and ciphertext token lengths agree. A mismatch with a reference corpus still does not identify a length-changing cipher: the text's genre, conversion rules, headings and boundary conventions can also differ. See [cipher invariants](#/wiki/cipher-invariants) and [search space and bounds](#/wiki/search-space).

## Reproduce the comparison

From a Liberpedia checkout or complete reproduction bundle, with an existing local corpus clone and a new output directory:

```text
python experiments/records/corpus-prefix-census/run.py /path/to/project-runeberg --output /path/to/new-corpus-replay
```

Python's standard library and Git are sufficient. The wrapper runs offline and stops when any stage fails. The [reproduction instructions](experiments/records/corpus-prefix-census/README.md) explain source retrieval, each output, and how to resume an interrupted census. The external corpus is not included in the reproduction bundle.

The source checker reads every distinct blob, independently reconstructs the token prefix and statistics, and checks every duplicate row. A second checker independently reconstructs all 46 comparison rows with exact ties. Only after both succeed does the renderer create the figure and tables. These are separate implementations within this project, not an external peer review.

## Sources and scope

The corpus is [mortlach/project-runeberg at revision a39e87e](https://github.com/mortlach/project-runeberg/tree/a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87). The earlier analysis is [mae3301/lp_experiments at revision cb5cdb9](https://github.com/mae3301/lp_experiments/tree/cb5cdb908bb34b68d8a05353eaace56e83d0bbf2). The census and comparison plans retain the counting conventions and input hashes fixed before the complete run.

This is a fresh implementation of a declared descriptive comparison. It does not execute the historical scripts, validate their entire statistical analysis, or reproduce an unavailable conversion pipeline.
