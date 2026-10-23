# Matrix, radix and grouping leads supplied on 22 October 2026

This is source intake, not a set of completed decryption experiments. Counts below were independently recomputed from Liberpedia's archived rune text and GP lookup. A count fitting a rectangle permits a layout but supplies neither its orientation nor a reading path.

Reproduce the count table with `python scripts/audit_cc_matrix_counts.py --check`; the [saved audit](cc-matrix-counts.json) includes the input hashes and all four representation lengths for each page group. The script does not inspect image colors, route choices or plaintext.

## CC's section matrices and two Page 15–22 PDFs

The supplied post proposes separate numerical grids for LP2 sections, followed by a route rule that might combine runes, GP primes, prime digits or rune indices. Its Stage 1 PDF is 19 pages, SHA-256 `e16b6f9b4d1d7d9bd87a1dfcc00fc3f9413aae3f7ad155e7157fda0fb914d817`; Stage 2 is six pages, SHA-256 `70bb9742fbb12439b6966c40d08c230325ab8fe87814de4dffcb8922805629ef`. The files were fetched from the two signed Discord CDN links in the submitted post on 22 October; those links may expire. These hashes identify the PDFs actually inspected, not a claim that they are author-approved permanent editions.

Source links as supplied: [Stage 1](https://cdn.discordapp.com/attachments/1562574777355345991/1562574778206912663/Liber_Primus_Beginner_Guide_15-22.pdf?ex=6adbce2a&is=6ada7caa&hm=48e6b38c081d453420ac1f390ead5d9dde8666af4bc29b799cb9e6d0bfafcb8b) and [Stage 2](https://cdn.discordapp.com/attachments/1562574777355345991/1562832499955212429/15-22_Stage_2_ROMANA.pdf?ex=6adb6cb0&is=6ada1b30&hm=c10b109e50bae7b6c051391a004b1ef83835067cb71c394d68092333323a12d0).

| Page group | Pinned count | Proposed fit | What the count establishes |
| --- | ---: | --- | --- |
| LP2-00–02 | 729 runes | 27 × 27 | Exact rune-count fit. Already used by the bounded [totient route replay](../../experiments/records/totient-map-route/record.json). |
| LP2-03–07 | 2,345 GP-prime decimal digits | 35 × 67 | Exact digit-count fit under unseparated prime values. |
| LP2-08–14 | 1,729 runes | 7 × 13 × 19 | Exact rune-count factorization. |
| LP2-08–14 | 2,915 digits of 1-based indices | 54 × 54 if an extra printed 7 is appended | The rune stream alone is **one digit short**. Inclusion and placement of the printed 7 are additional choices. |
| LP2-15 body | 150 runes; 289 GP-prime digits | 17 × 17 digits | Excludes the nine-rune header but keeps the eleven red body runes. Omitting all red runes would not give this square. |
| LP2-16–22 | 1,744 runes; 3,481 GP-prime digits | 59 × 59 digits | Exact digit-count fit with all seven pages concatenated. |
| LP2-23–26 | 1,021 runes total | 15 × 67 = 1,005 if 16 red runes are excluded | The subtraction is exact; the color selection still needs an image-level source trace. |
| LP2-27–31 | 1,312 runes; 2,200 digits of 0-based indices | 32 × 41 runes; 44 × 50 index digits | Both arithmetic fits reproduce under different representations. |
| LP2-32 | 121 runes; 196 digits of 0-based indices | 11 × 11 runes; 14 × 14 index digits | Both arithmetic fits reproduce. |
| LP2-33–39 | 1,680 runes | 40 × 42 or 7 × 15 × 16 | Exact total count; 33–38 contributes 1,440 = 36 × 40 and page 39 contributes 240 = 15 × 16. |

Stage 1 reconstructs the 4 × 4 printed Page 15 panel using Fibonacci-indexed primes around 3301, then makes two digit spirals. The panel construction is independently covered by the [Fibonacci panel audit](../../exports/fibonacci-prime-panel.json). Stage 1 expressly corrects an earlier “150 black runes” wording: eleven of those 150 body runes are red. The five proposed readings FORK, DEDUCED, ROMANA, TO and HALFMAN come from an inherited substitution **reconstructed from those same word pairs**; reproduction of the pairs is not an independent key prediction.

Stage 2 freezes a more elaborate conditional chain: transpose the printed square; select seven spiral positions; take each number's final two decimal digits; convert each to Roman numerals; keep the first symbol; apply the HALFMAN ordering. Its seven symbols have values 50, 10, 50, 50, 50, 10, 5, summing to 225. The corresponding original prime ranks 5, 8, 13, 21, 34, 55, 89 also sum to 225. The PDF reports comparisons with the printed layout, other windows, inverse permutation and eight square symmetries. These arithmetic checks are reproducible from the stated values, but the selection chain and any use as a decoding instruction remain unproved. No continuation to independently selected pages or complete plaintext is supplied. A replay should freeze the entire selection procedure, reproduce every Stage 1 and Stage 2 intermediate, then evaluate the **best** result of the full allowed search on controls; a fresh section should be held out if the rule is used as a cipher claim.

## Totient-map discussion extract

Source text SHA-256 `976d41e4fb70be241b1d3d0f9e17b94a8bc4029f4dae93944c1319d56e071e74` (`84c107dc-480c-4fe2-bb17-30613846863c`). Most of this discussion overlaps the already published [27 × 27 totient-route replay](../../experiments/records/totient-map-route/record.json) and should not be counted again as a new attempt. One distinct numerical claim compares selected seven-word LP1 spans to the proposed phrase “AS I GO THE WEATHER TURNS COLD”: both allegedly have 21 runes and GP sum 825, with index sums 232 and 233. The claim further says the chosen LP1 match is unique among 716 seven-word windows. To check it, fix the exact LP1 text layer, word-boundary convention, spelling and whether 716 is the correct denominator, enumerate every eligible window, and compare the whole selection process rather than just the chosen pair. The numbers and alleged uniqueness have **not** been verified in this intake. The surrounding literary interpretation is not a ciphertext result.

## Group statistics and base-59 discussion extract

Source text SHA-256 `1cac35c91551b3278227b4cca1fe2c88f1c96734cfc067bd9560a9445d26ca5d` (`d11e8f14-5377-4a7e-bc54-ffd53a98e102`). It proposes comparing IoC and doublet patterns by manuscript section, especially LP2-40–53 or 40–55 against LP2-54–55; and it reports a repeated sequence on LP2-27 and LP2-55 at stated offsets. A bounded replay must pin the exact grouping, rune layer, offset convention, statistic, and controls that account for different group lengths. Broad remarks about different ciphers or intent are hypotheses, not measurements.

The same discussion moves between base-59, base-60 and base-62 analyses of the alphanumeric grids. It says 59 distinct characters appear and lowercase `f` is absent. **A count of distinct characters does not determine the radix**: with the conventional case-sensitive digit ordering, a present `x` has value 59 and requires base at least 60, even when fewer than 60 symbols happen to occur. One quoted script in the same extract reaches that base-60 minimum. Another later report uses base 62. These changing conventions must be separated before any decoded bytes or statistical test are compared. The [alphanumeric-grid guide](../../articles/alphanumeric-grids.html) documents the standard ordering and its byte-width assumption; this intake does not independently replay the source's 256-token dump or its downstream transformations.

Disposition: queue the CC traversal and Roman-selector chain as one related family with explicit Stage 1 and Stage 2 variants; queue the LP1 word-window census and the sectionwise statistics as separate bounded checks. Treat the base-59 claim as a radix-convention reconciliation. None of these entries increases the number of completed experiments.
