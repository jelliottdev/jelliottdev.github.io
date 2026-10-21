# Corpus-prefix comparison: rules fixed before the full census

This is a follow-up to the descriptive census, not a change to its counting rules. Execution is pending. The historical manuscript summary, twelve convenience-sample prefixes and source inventory have already been inspected. Partial census checkpoints exist. No full-corpus tail calculation has been run. This is a project-level declaration, not an externally registered or fully blinded study.

## Question and reference population

Where does the reconstructed historical 2,902-token manuscript summary fall within the complete pinned corpus of eligible 2,902-token prefixes? Use every eligible path in the independently audited census. Preserve the original file weights, including byte-identical paths. Report a second, explicitly labeled sensitivity with each distinct Git blob counted once. This is byte deduplication, not deduplication of works, editions or translations.

Use `runes_plus_single_digits` from the pinned manuscript report. It contains 2,896 rune tokens plus six isolated decimal digits counted as length one. This reproduces the historical summary; it does not establish the historical author's exact parser. Do not substitute the rune-only ledger midway through this comparison.

## Measures and ties

Publish every selected measure, in fixed order: frequencies of lengths 1 through 14, frequency of lengths 15 and above, mean, sample variance, sample standard deviation, minimum, lower quartile, median, upper quartile and maximum. These are 23 descriptive comparisons, not 23 independent tests. The grouped 15+ frequency retains the reference population's longer tokens even though the manuscript has none.

For each measure retain the reference count strictly below the manuscript value, equal to it, and strictly above it. Report both inclusive fractions `(below + equal) / eligible` and `(above + equal) / eligible`, with integer numerators and denominators. Their sum exceeds one when there are ties. Do not silently replace an inclusive tail with its complement.

Reconstruct frequencies, means, variances and interpolated quartiles from integer histograms using exact rational arithmetic. For standard-deviation ordering and ties compare variances, since square root is strictly increasing on nonnegative values. Do not decide ties using rounded CSV values or floating tolerances. Require histogram totals and source/report hashes to agree with the audited census.

## Interpretation and presentation

Show all comparisons for both weighting policies; do not select only the smallest fraction. These are empirical positions in a fixed, nonrandom collection of file prefixes. They are not calibrated hypothesis-test p-values, language probabilities, or a probability that the manuscript is natural language. No multiple-testing rejection decision or combined anomaly score is planned. Any later inferential test needs a separate justified sampling model and declared selection procedure.

Keep the unit mismatch visible: corpus tokens count all retained Unicode code points under the historical literal-space rule, whereas the reconstructed manuscript uses rune units plus six digits. The converter and edition manifest are unavailable. This comparison reproduces a defined numerical question; it does not repair those provenance limits or validate a language identification.

Before publication, require the full census's independent source-byte audit, an independent reconstruction of the comparison counts, exact input hashes, all 23 result rows, and a reproduction command. A figure should show the distributions or empirical ranks across all measures without singling out a preferred language. There is no language classification in this experiment.
