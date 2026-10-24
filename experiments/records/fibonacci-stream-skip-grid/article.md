None of the tested Fibonacci keys produced a complete-page result that passed the English-score test. The search checked every starting pair for the specified modulo-29 recurrence. Of 92,510 distinct settings, 900 advanced from a short check to complete-page decoding. 

## The Fibonacci rule

The recurrence is F(0)=a, F(1)=b and F(n+2)=(F(n+1)+F(n)) modulo 29, for all 841 seed pairs. The source also tests signs -1/+1, offsets 0 through 4 and both ciphertext Atbash settings on all 55 rune-bearing LP2 pages. Its first 50 runes use a width 60 beam. Only normalized scores strictly above -6.5 receive full-page width 200 decoding, with a final strict -5.5 gate. Rejected short settings are not decoded as complete pages. F is an ordinary rune, and state resets for each page.

## Equivalent settings

The alias reduction preserves exact source behavior. For source sign s and offset o, define G[j]=sF[j+o] mod 29. It is the same recurrence with seed pair (sF[o],sF[o+1]), sign+1 and offset 0. The shift matrix [[0,1],[1,1]] has determinant -1 modulo 29; each fixed sign/offset maps all 841 pairs bijectively. Each canonical setting therefore has exactly 10 source-label aliases. Atbash is retained both ways because this identity does not remove its ciphertext reflection.

Finite keys and ties do not break the identity. Arrays have exactly 1,176 slots. A 277-rune page can reach original key index 1108 at most; the source's padding requirement is at most 1120, below 1,176. Translating each pointer by minus the offset preserves plaintext, every rejected-key equation, cumulative scores and candidate enumeration order. The stable score-only sort and first-maximum selection preserve tied paths and ordered terminal beams. Original label ordinals are expanded when choosing a tied best label or reporting source counts.

Before target execution, the saved proof checks all 8,410 seed/sign/offset mappings across their entire available aligned prefixes. A frozen synthetic preflight then verifies native source 50-rune parity for every mapping, plus 120 full 277-rune representative and tie-heavy comparisons, including entire ordered terminal beams. An independent reviewer verifies the same finite identities and bounds. No manuscript ciphertext enters these parity tests.

## Known-message controls

All 841 canonical keys also receive a fixed known-reading control: alternate the existing 184-rune Warning and 85-rune LP2-56 readings, use the source encoder with suppression 0.83, and choose the first seed 3301 through 3332 whose maximum skipped run is at most 3. All 841 find an eligible plant, requiring at most 10 attempts; 21 have zero skips. All 841 pass both score gates, but 805 recover the complete reading exactly. The 36 mismatches retain the valid true reading in the final beam at ranks 2 through 4. Every chosen alternative has a strictly higher cumulative score; four have a worse normalized score than the truth. There are no ties or missing true paths in these failures. Recognition by the source gates is therefore distinct from exact recovery. The seed policy conditions on bounded skips and does not establish a full-search false-positive rate.

## Inputs and implementation

The target plan freezes the source, model, proof, control receipts and all manuscript inputs before new target calls. Source rune arrays match LP2-00 through 49 and 51 through 55 exactly, including headings. The blank LP2-50 has no rune stream. The imported module's incomplete bigram prefilter setup is unused; these direct beam calls score with the exact committed English quadgram model. No source beam or scoring correction is introduced. A 32-key synthetic benchmark projects about 58 seconds of short screens at its measured mean, with confirmations extra. The target completes in 91.9 seconds.

## Full-page results

The 900 canonical full decodes represent 9,000 expanded source labels. The best returned complete score is -6.306038765432711, for canonical seed (13,7), LP2-55, Atbash enabled. It does not pass the final gate. The saved source-label summaries preserve the original source ordering rather than treating aliases as independent candidates.

## Checking the other retained candidates

After observing the source outputs, a separately frozen POST-TARGET audit scores all 160,613 retained terminal hypotheses. In 778 settings another retained path has a better normalized score than the source's cumulative-score winner. None crosses -5.5. The best normalized terminal score is -6.276971493386715, for canonical seed (17,21), LP2-55, Atbash disabled. This audit preserves the historical source outputs and does not rerank intermediate beams, recover pruned paths or fully decode rejected screens.

## Reproduce and verify

A separately implemented checker rescores all 92,510 short outputs, reconstructs every 900 returned full path and the ten best short paths, and independently rescores and verifies a legal key-pointer path for all 900 best-normalized terminal witnesses. It recounts aliases, expanded labels, gates and tied-label order. Another isolated portable replay repeats all 841 source plants and the full target, reproducing cases, binary short paths and expanded-label summaries byte-for-byte; only wall time differs. The original plans and outputs remain unchanged. The optional replay flag --parity repeats the full native synthetic parity grid as well.

## Scope and sources

The figure uses an actual alias of the best returned full setting: seed (4,19), offset 3 starts 13,7,20,..., exactly like canonical seed (13,7), offset 0. The funnel shows actual computed settings, not independent evidence counts. The source files are pinned to Dukotah/cicada 3301 commit f08b20b632d91209ddbaa747e8e2f23df0c78ba1, with its MIT license bundled. This is a bounded source computation and control study: no plaintext is certified, no global probability is calibrated, and no general numeric-key or OTP conclusion follows. Other keys, clocks, languages, joined-page rules and intermediate ranking criteria remain outside scope.
