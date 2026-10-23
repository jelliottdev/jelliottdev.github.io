# Matrix, radix and grouping leads supplied on 22 October 2026

This is source intake, not a set of completed decryption experiments. Counts below were independently recomputed from Liberpedia's archived rune text and GP lookup. A count fitting a rectangle permits a layout but supplies neither its orientation nor a reading path.

Reproduce the count table with `python scripts/audit_cc_matrix_counts.py --check`; the [saved audit](cc-matrix-counts.json) includes the input hashes and all four representation lengths for each page group. The script does not inspect image colors, route choices or plaintext.

## CC's section matrices and two Page 15–22 PDFs

The supplied post proposes separate numerical grids for LP2 sections, followed by a route rule that might combine runes, GP primes, prime digits or rune indices. Its Stage 1 PDF is 19 pages, SHA-256 `e16b6f9b4d1d7d9bd87a1dfcc00fc3f9413aae3f7ad155e7157fda0fb914d817`; Stage 2 is six pages, SHA-256 `70bb9742fbb12439b6966c40d08c230325ab8fe87814de4dffcb8922805629ef`. The files were fetched from the two signed Discord CDN links in the submitted post on 22 October; those links may expire. These hashes identify the PDFs actually inspected, not a claim that they are author-approved permanent editions.

The two supplied PDFs are not hosted on Liberpedia. Their SHA-256 hashes above identify the versions used for this replay.

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

Source text SHA-256 `976d41e4fb70be241b1d3d0f9e17b94a8bc4029f4dae93944c1319d56e071e74` (`84c107dc-480c-4fe2-bb17-30613846863c`). Most of this discussion overlaps the already published [27 × 27 totient-route replay](../../experiments/records/totient-map-route/record.json) and should not be counted again as a new attempt. One distinct numerical claim compares a selected seven-word LP1 span to the proposed phrase “AS I GO THE WEATHER TURNS COLD”: both reportedly have 21 runes and GP sum 825. The [LP1 window census](lp1-seven-word-825-audit.md) confirms one 21-rune, GP-825 match in the shipped solved-rune trace, at warning word 9, with index sum 232. It finds 652 section-internal seven-word windows, not the reported 716. This does not establish the proposed LP2 phrase or a probability of deliberate linkage; those depend on a separately fixed rune spelling and the full selection process. The surrounding literary interpretation is not a ciphertext result.

## Group statistics and base-59 discussion extract

Source text SHA-256 `1cac35c91551b3278227b4cca1fe2c88f1c96734cfc067bd9560a9445d26ca5d` (`d11e8f14-5377-4a7e-bc54-ffd53a98e102`). It proposes comparing IoC and doublet patterns by manuscript section, especially LP2-40–53 against LP2-54–55. The [sectionwise profile](../../experiments/records/sectionwise-rune-profile/record.json) compares the ending to equal-length earlier windows; neither measure lies outside their middle 95% range. The [DJU-BEI record](../../experiments/records/dju-bei-cross-page/record.json) locates the reported rune sequence once on each of LP2-27 and LP2-55 under explicit offsets. Those observations do not by themselves identify a shared cipher or page connection. A separate [lag-13 test](../../experiments/records/short-window-lag13/record.json) operationalizes an underspecified short-window motif from another supplied post; it does not purport to replay exact historical coordinates.

The same discussion moves between base-59, base-60 and base-62 analyses of the alphanumeric grids. The [radix reconciliation](../../experiments/records/grid-radix-reconciliation/record.json) confirms 59 observed characters among 256 pairs, with lowercase `f`, `y` and `z` absent. **The count alone does not determine the radix.** Under ordinary `0–9 A–Z a–z` ordering, `x` has value 59, so conventional base 59 is invalid and base 60 is the minimum. A *custom* 59-digit alphabet that deletes the unused `f` is also valid for byte-sized pairs, but renumbers later lowercase symbols and changes 220 of the 256 token values. The supplied and archived token lists differ at five coordinates. Any downstream byte or statistical claim must pin its alphabet, token list and byte assumption; neither valid representation alone supplies a cipher rule.

Disposition: the CC selector, LP1 window census, sectionwise statistics and radix convention now have separate bounded checks. They remain distinct from claims of a solved page or identified encryption mechanism.
