# Does the Cypherpunk Manifesto read as an LP2 running key?

**This specific running-key test did not produce a convincing whole-page reading.** We tried every contiguous offset of a pinned copy of Eric Hughes’s *A Cypherpunk’s Manifesto* against [LP2-00](#/reader/lp2-00), [LP2-31](#/reader/lp2-31) and [LP2-54](#/reader/lp2-54). Under both declared ways of turning its letters into key values, each page’s best score was matched or beaten by several fully searched shuffled keys. The same search ranked a planted known reading first under **both** mappings.

![Whole-page scores for two manifesto key mappings on three LP2 pages against fully searched shuffled-key controls](experiments/records/cypherpunk-manifesto-running-key/whole-page-scores.svg)

## What was tested

The [source page](https://activism.net/cypherpunk/manifesto.html) is attributed to Eric Hughes and dated 9 March 1993. We preserved the HTML bytes retrieved on 23 October 2026 and used only its essay body, from the first “Privacy is necessary” through “Onward.” The title, signature, address and date were excluded. Uppercasing and retaining A–Z leaves **4,072 letters**. The source URL, raw and normalized hashes, and exact extraction rule are in the [plan](experiments/records/cypherpunk-manifesto-running-key/plan.json).

We tested two **different alphabet assumptions**, named in the figure:

- **A–Z shifts:** A=0 through Z=25, one letter per key step. This matches the convention in the [Emerson running-key test](#/experiments/emerson-running-key); it is not itself a GP transcription.
- **GP rune key:** Parse the letters greedily as canonical Gematria Primus Latin labels, including TH, NG and other two-letter labels, with V/K/Z/Q mapped to U/C/S/C. This produces **3,893 key units**. Erasing the source’s spaces permits a two-letter label to cross a former word boundary; another boundary policy is outside this test.

For each mapping and each of the three pages, we tried **every zero-based offset** leaving enough key units to cover the **entire page**. At each rune position we calculated `plaintext = ciphertext − key (mod 29)`, joined the resulting GP Latin labels, and used the pinned English quadgram score. The three page lengths are 262, 269 and 232 runes. The source and the sixteen shuffled copies were searched with exactly the same offsets and score. The shuffles preserve each mapping’s key-value counts; they do not model alternative meaningful books.

## Result and limit

For A–Z shifts, **13, 16 and 13** of the sixteen shuffled-key searches equalled or beat the manifesto’s best whole-page score on LP2-00, 31 and 54. For the GP rune key the counts were **11, 14 and 9**. Those are comparisons of *maxima from complete offset searches*, so a lucky offset is compared with other equally searched opportunities. The figure shows the score and full shuffle range for each case; the [result file](experiments/records/cypherpunk-manifesto-running-key/results.json) retains all top-five offsets and decoded strings.

Before examining LP2, we encoded the full 264-rune known reading on LP1-04 using each mapping at offset 3301. In both cases, the identical exhaustive search selected that offset first and recovered the planted reading exactly. This checks the decoder and scorer on a known plaintext. It cannot establish that either mapping is the one used by LP2.

Sixteen shuffled searches give a coarse reference, not a calibrated tail probability. The English scorer can also miss meaningful non-English or unusually rendered plaintext. The result is confined to this archived edition, these two mappings, subtraction direction, page-start clock, three target pages and whole-page English scoring. It does **not** rule out the manifesto under a different rule or running keys in general.

## Reproduce

Download this record’s files and run `python experiments/records/cypherpunk-manifesto-running-key/run.py --check` from the repository root. The independent `check.py` parses the source with a separate HTML parser and recomputes every original and shuffled offset maximum. `plot.py --check` verifies the figure. All three scripts use Python’s standard library and the pinned files; they do not fetch the source again.
