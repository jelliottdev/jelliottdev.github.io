## The question this comparison asks

An earlier word-length analysis compared the unsolved manuscript with thousands of converted texts. Before interpreting a reported rarity, we need to know what was counted, which texts entered the comparison, and whether repeated files received repeated weight.

This experiment asks a specific descriptive question: **where does the reconstructed 2,902-token manuscript summary fall among the first 2,902 tokens of every eligible file in the pinned reference corpus?** It does not ask which language is most likely. The separate [parallel-language experiments](#/experiments/parallel-languages) compare aligned translations under declared representations.

## What the complete audit found

The census covers all **25,906 paths** and **25,844 distinct source blobs**. Of these, **25,565 paths** are long enough for the declared prefix, representing **25,563 distinct eligible blobs**. The other 341 paths are retained as ineligible rows. Every source object and all 46 comparison rows passed the separate checks.

The manuscript has 448 length-two tokens out of 2,902. Only 138 eligible prefixes have a smaller proportion, and one ties it: the inclusive fraction at or below is **139/25,565 (about 0.544%)**. Its 720 length-three tokens give a different position: 24,171 prefixes fall below that proportion, 29 tie it and 1,365 fall above it. These are descriptive counts within this reference collection, not chances that a language or cipher hypothesis is true.

Other measures need not be extreme. The manuscript's variance has 10,995 prefixes below it and 14,570 above it. Its minimum token length of one ties every eligible prefix. Its lack of tokens of length 15 or more is shared by 13,205 prefixes. The complete tables retain these ordinary and tied observations alongside the more unusual proportions.

Removing byte-identical duplication reduces the eligible denominator by only two. For the length-two proportion, the below and equal counts remain 138 and one; the above count changes from 25,426 to 25,424. This sensitivity removes duplicate bytes, not all related works.

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

The [provenance note](experiments/records/corpus-prefix-census/PROVENANCE.md) preserves a frozen test-file hash and documents corruption checks added later. The calculation and audit code match their recorded hashes.

This is a fresh implementation of a declared descriptive comparison. It does not execute the historical scripts, validate their entire statistical analysis, or reproduce an unavailable conversion pipeline.

## Complete corpus comparison

Every planned measure is shown under both weighting rules. Bars partition reference prefixes by whether their value is below, equal to, or above the manuscript value. They do not show probabilities of a language or cipher.

The two inclusive fractions both contain ties: they can sum to more than one. Distinct Git blobs remove byte-identical duplicates only; editions, translations and overlapping works may remain. Manuscript values are exact fractions; length-bin values are proportions. Standard deviation is shown as a square root, while its ranks use exact variance ordering, which preserves all ties.

### Every eligible path

| Measure | Manuscript value | Below | Equal | Above | At or below | At or above |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Length 1 | 89/2902 | 4971 | 192 | 20402 | 5163/25565 | 20594/25565 |
| Length 2 | 224/1451 | 138 | 1 | 25426 | 139/25565 | 25427/25565 |
| Length 3 | 360/1451 | 24171 | 29 | 1365 | 24200/25565 | 1394/25565 |
| Length 4 | 513/2902 | 21752 | 87 | 3726 | 21839/25565 | 3813/25565 |
| Length 5 | 317/2902 | 16047 | 201 | 9317 | 16248/25565 | 9518/25565 |
| Length 6 | 128/1451 | 15235 | 333 | 9997 | 15568/25565 | 10330/25565 |
| Length 7 | 108/1451 | 18726 | 172 | 6667 | 18898/25565 | 6839/25565 |
| Length 8 | 78/1451 | 19949 | 191 | 5425 | 20140/25565 | 5616/25565 |
| Length 9 | 39/1451 | 8958 | 262 | 16345 | 9220/25565 | 16607/25565 |
| Length 10 | 26/1451 | 13985 | 384 | 11196 | 14369/25565 | 11580/25565 |
| Length 11 | 16/1451 | 16219 | 509 | 8837 | 16728/25565 | 9346/25565 |
| Length 12 | 9/1451 | 19595 | 717 | 5253 | 20312/25565 | 5970/25565 |
| Length 13 | 2/1451 | 10212 | 2696 | 12657 | 12908/25565 | 15353/25565 |
| Length 14 | 3/2902 | 17826 | 2942 | 4797 | 20768/25565 | 7739/25565 |
| Length 15+ | 0 | 0 | 13205 | 12360 | 13205/25565 | 25565/25565 |
| Mean | 6481/1451 | 20282 | 12 | 5271 | 20294/25565 | 5283/25565 |
| Variance | 22676602/4209351 | 10995 | 0 | 14570 | 10995/25565 | 14570/25565 |
| Standard deviation | √(22676602/4209351) | 10995 | 0 | 14570 | 10995/25565 | 14570/25565 |
| Minimum | 1 | 0 | 25565 | 0 | 25565/25565 | 25565/25565 |
| Lower quartile | 3 | 24200 | 1341 | 24 | 25541/25565 | 1365/25565 |
| Median | 4 | 7318 | 17880 | 367 | 25198/25565 | 18247/25565 |
| Upper quartile | 6 | 11066 | 12294 | 2205 | 23360/25565 | 14499/25565 |
| Maximum | 14 | 4766 | 8439 | 12360 | 13205/25565 | 20799/25565 |

### Distinct eligible Git blobs

| Measure | Manuscript value | Below | Equal | Above | At or below | At or above |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Length 1 | 89/2902 | 4970 | 192 | 20401 | 5162/25563 | 20593/25563 |
| Length 2 | 224/1451 | 138 | 1 | 25424 | 139/25563 | 25425/25563 |
| Length 3 | 360/1451 | 24170 | 29 | 1364 | 24199/25563 | 1393/25563 |
| Length 4 | 513/2902 | 21750 | 87 | 3726 | 21837/25563 | 3813/25563 |
| Length 5 | 317/2902 | 16046 | 201 | 9316 | 16247/25563 | 9517/25563 |
| Length 6 | 128/1451 | 15234 | 333 | 9996 | 15567/25563 | 10329/25563 |
| Length 7 | 108/1451 | 18724 | 172 | 6667 | 18896/25563 | 6839/25563 |
| Length 8 | 78/1451 | 19947 | 191 | 5425 | 20138/25563 | 5616/25563 |
| Length 9 | 39/1451 | 8957 | 262 | 16344 | 9219/25563 | 16606/25563 |
| Length 10 | 26/1451 | 13984 | 384 | 11195 | 14368/25563 | 11579/25563 |
| Length 11 | 16/1451 | 16218 | 509 | 8836 | 16727/25563 | 9345/25563 |
| Length 12 | 9/1451 | 19594 | 717 | 5252 | 20311/25563 | 5969/25563 |
| Length 13 | 2/1451 | 10212 | 2696 | 12655 | 12908/25563 | 15351/25563 |
| Length 14 | 3/2902 | 17824 | 2942 | 4797 | 20766/25563 | 7739/25563 |
| Length 15+ | 0 | 0 | 13204 | 12359 | 13204/25563 | 25563/25563 |
| Mean | 6481/1451 | 20280 | 12 | 5271 | 20292/25563 | 5283/25563 |
| Variance | 22676602/4209351 | 10994 | 0 | 14569 | 10994/25563 | 14569/25563 |
| Standard deviation | √(22676602/4209351) | 10994 | 0 | 14569 | 10994/25563 | 14569/25563 |
| Minimum | 1 | 0 | 25563 | 0 | 25563/25563 | 25563/25563 |
| Lower quartile | 3 | 24199 | 1340 | 24 | 25539/25563 | 1364/25563 |
| Median | 4 | 7317 | 17879 | 367 | 25196/25563 | 18246/25563 |
| Upper quartile | 6 | 11065 | 12293 | 2205 | 23358/25563 | 14498/25563 |
| Maximum | 14 | 4766 | 8438 | 12359 | 13204/25563 | 20797/25563 |

