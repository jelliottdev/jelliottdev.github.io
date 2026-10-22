# How much do unresolved LP2 page joins change word-length counts?

The published LP2 word-length census joins adjacent pages when their archived text meets rune to rune. That rule yields **2,896 rune tokens**. If a separator is inserted at each of the **32 rune-to-rune page edges**, the same 12,956 runes yield **2,928 tokens**. This experiment measures how much the statistics depend on that parsing choice. It does not decide which edges actually split words in the manuscript.

![Side-by-side rune-token length counts for joined and separated page edges](experiments/records/page-join-sensitivity/token-lengths.svg)

## Fixed comparison

Use the archived text for LP2-00–55 and the site's 29-rune alphabet. Remove slash and CR/LF row wraps, retain headings and other punctuation, and count rune runs with optional internal apostrophes. There are three prespecified readings: concatenate every page; insert a space at all 32 edges whose archived end and start are both runes; and insert a space at each such edge one at a time. No rune is changed or omitted. The [boundary inventory](#/wiki/transcription-checking?section=page-joins) supplies the distinction between a rune-to-rune candidate and a verified word join.

| Measure | All edges joined | All 32 candidates separated |
| --- | ---: | ---: |
| Rune tokens | 2,896 | 2,928 |
| One-rune tokens | 83 | 99 |
| Two-rune tokens | 448 | 465 |
| Three-rune tokens | 720 | 726 |
| Tokens at least 10 runes long | 109 | 104 |
| Maximum token length | 14 | 14 |
| 11–11–10 length windows | 1 | 1 |

All 32 individual splits add exactly one token under this tokenizer. Five individual edges—LP2-21/22, 24/25, 42/43, 46/47 and 52/53—each reduce the number of tokens at least 10 runes long by one. The [machine-readable result](experiments/records/page-join-sensitivity/results.json) lists every edge separately. The LP2-21 11–11–10 observation survives both endpoint policies, but this says nothing about its chance frequency or interpretation.

These endpoints are sensitivity cases, not manuscript corrections. A real reading could join some edges and split others. The source text can also omit a mark, and rune-to-rune edges can cross section boundaries. Word counts, repeated-token counts and word-reset cipher inputs depend on the boundary rule; rune frequencies and whole-stream IoC do not, because both versions contain the identical ordered runes. The reported 2,896 tokens are a transparent parsing convention, not 2,896 established words.

## Reproduce and extend

With Python 3 and no packages, run `python experiments/records/page-join-sensitivity/run.py --check` and `python experiments/records/page-join-sensitivity/check.py` from the repository root or the [experiment bundle](downloads/experiments/page-join-sensitivity.zip). The first command checks the source hashes, complete report and figure. The second uses an independent character scanner to verify the 32 candidate edges, the two histograms, every one-edge token count, and the invariant 12,956-rune total. The plan fixes the inputs and three comparisons before interpreting them.

The next useful refinement is to record image-reviewed separators at particular edges and rerun the same script with those decisions frozen. Until then, a word-based cipher claim should specify its page-edge policy and show whether its result survives plausible changes at the relevant edges. See the [word-length guide](#/wiki/word-lengths) for the counting rules and complete token ledger.
