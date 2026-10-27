/* Reviewed editorial navigation only. No method capability or scientific finding is inferred. */
(function(root){
 'use strict';
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const LABELS=freeze({'method:repeating-key':'Repeating-key shifts','method:running-key':'Non-repeating key shifts','method:feedback':'Rune feedback','method:generated-key':'Other keyed rules','method:numeric':'Combine rune streams','method:direct-mapping':'Direct value mapping','method:payload':'Data-format checks','method:public-key':'Public-key checks'});
 // Exact reviewed procedure and parameter text prevents edits inheriting stale method claims.
 const DESCRIPTIONS=freeze({'method:repeating-key':'Add or subtract a key that repeats.','method:running-key':'Add or subtract successive key values without wrapping.','method:feedback':'Use earlier input or decoded runes in later steps.','method:generated-key':'Use other fixed rules for applying a key.','method:numeric':'Add, subtract or combine two rune streams.','method:direct-mapping':'Apply fixed numeric mapping rules.','method:payload':'Try specified encodings, decoders and format checks.','method:public-key':'Apply public-key arithmetic and check defined padding.','method:other-decoding':'Other decoding rules awaiting a more specific method grouping.'});
 const REVIEWED=freeze({
  "alternating-alphabet-interruption-clocks": {
    "bucket": "method:repeating-key",
    "procedure": "Alternate ordinary/reversed cipher alphabets, each with its own known repeating key. Decode F normally but hold the selected key position there. Compare always-toggling versus F-paused alphabet clocks; compare each head with nine fixed twelve-rune known-reading openings.",
    "parameters": "2 key assignments × 104 phase pairs × 2 first alphabets × 2 signs × 2 clock policies = 1,664 settings; 55 pages; 823,680 exact comparisons. 1,664 roundtrips on 87 prescribed runes plus 1,664 forced-marker controls."
  },
  "b04-source-seeds-opening-cribs": {
    "bucket": "method:generated-key",
    "procedure": "Regenerate the pinned source seed bytes through 16 source generators and five reductions. For every forward/reverse stream, sign and ciphertext-Atbash setting, exactly test whether any key-skip path can produce a fixed opening; no English score or beam pruning.",
    "parameters": "2,165 seeds × 16 generators × 5 reductions × two directions × two signs × two Atbash states = 1,385,600 configurations; zero offset; at most three rejected draws per emitted rune; all 55 nonempty LP2 page starts; nine fixed 12-rune cribs."
  },
  "block-lookahead-feedback": {
    "bucket": "method:feedback",
    "procedure": "For b in {5,7}, encode and exactly recover each known LP1 reading. Decode LP2 pages under the fixed future-plaintext block-start equation; save full-page digests, IoC, F count and 12-rune known-opening comparisons.",
    "parameters": "k[i]=0; b=5 or 7; page-local phase zero; terminal future plaintext=0; modulo 29; 55 nonempty LP2 targets times 15 fixed known openings per case."
  },
  "crib-inferred-feedback-table": {
    "bucket": "method:feedback",
    "procedure": "For each fixed 12-rune opening, infer f(previous ciphertext) or f(previous plaintext) from C_i−P_i modulo29 at i=1..11. Reject conflicting assignments, count 29^(29−r) full extensions for r assigned inputs, and measure coverage on the next twelve ciphertext positions without a truth label.",
    "parameters": "2 feedback modes × 55 page starts × 9 fixed openings = 990 partial-table inferences; 11 constraints per proposed opening; 29 possible input slots."
  },
  "cumulative-autokey-literal": {
    "bucket": "method:feedback",
    "procedure": "Apply the stated cumulative formula, verify each reconstructed prefix, and compare 29-bin profiles with raw LP2 and solved LP1.",
    "parameters": "No fitted parameters; 55 nonempty pages, 12,956 runes; first rune retained per page."
  },
  "cypherpunk-manifesto-running-key": {
    "bucket": "method:running-key",
    "procedure": "At every no-wrap contiguous offset that covers the complete target page, subtract one key unit per rune modulo 29. Rank full-page English quadgram scores. Repeat the entire offset search on sixteen seeded value-shuffled keys per mapping/page. Plant an LP1-04 known reading with each mapping at offset 3301 and require rank one before LP2 scoring.",
    "parameters": "Two named source mappings; LP2-00 (262 runes), LP2-31 (269), LP2-54 (232); 3,804–3,841 A–Z offsets and 3,625–3,662 GP offsets per page; 16 complete shuffled-key searches for every mapping/page; one fixed subtraction direction and scorer."
  },
  "d4v1-column-unigram-key-recovery": {
    "bucket": "method:repeating-key",
    "procedure": "For each page and fixed KL2,3,5, remove source-listed possible-interrupter positions for column inference only; select each of29 shifts by source solved-page unigram target; apply the inferred key to the original page, then apply the separately pinned English quadgram score. Plant exact known texts and repeat the full 165-setting search on199 pagewise shuffled controls.",
    "parameters": "3 fixed periods ×55 rune-bearing pages =165 outputs; 9 complete-reading plants, 165 page-length plants, 199 full-search shuffle replicates, English line −5.5."
  },
  "d4v1-positional-totient-streams": {
    "bucket": "method:running-key",
    "procedure": "Apply P_i=(C_i−φ(i+offset)) mod29 for offsets 0–99 to each full page, score canonical GP Latin output with a pinned English quadgram model, calibrate with nine readings and offset-17 planted encryptions, and compare the global best with 199 full-search pagewise shuffles.",
    "parameters": "100 offsets × 55 pages = 5,500 outputs; −5.5 English line; nine solved readings; 199 full-search shuffled trials."
  },
  "decimal-chain-opening-cribs": {
    "bucket": "method:running-key",
    "procedure": "Enumerate five-digit decimal primers 00000..99999. Extend each by d_i=(d_(i-5)+d_(i-4)) mod10, decode with C_i plus or minus digit modulo29, and compare nine predeclared 12-rune openings at each page start.",
    "parameters": "100,000 primers × two signs × 55 rune-bearing pages × nine openings = 99,000,000 logical exact comparisons; complete prefix histogram; zero key offset; page-local reset."
  },
  "dukotah-b04-full-source-replay": {
    "bucket": "method:generated-key",
    "procedure": "Run G1/G2 source controls, full A/B/C seed-generator grids with English quadgram scorer and soft key-skip beam, then replay the source-selected 150 settings on both long targets. Independent checker validates saved merge, hashes and direct source-decoder comparisons.",
    "parameters": "2,165 A seeds, 504 B/C core seeds, 16 generators, source reduction/sign/Atbash/direction/offset axes, beam width 400, max three skips per rune, fixed score bar −5.5; 6,224,000 opening decodes and 300 D cells."
  },
  "dukotah-ciphertext-feedback-coefficients": {
    "bucket": "method:feedback",
    "procedure": "Run unchanged D-04 source full default grid, parse source stdout and independently reconstruct/rescore each winning feedback term. Separately search all 112 one-tap configurations for each of two declared in-domain plants.",
    "parameters": "28 one-tap, 840 two-tap and 4,204 three-tap coefficient vectors; const0/const1 seeds, signs +/-1, offset0, source English-scored beam width250 and max three skips; 60,864 page decodes total."
  },
  "dukotah-fixed-numeric-keys": {
    "bucket": "method:generated-key",
    "procedure": "Run the unmodified B1, B4 and C2 source scripts from one isolated copy. Independently reconstruct their fixed GP29 key streams, both signs, Atbash and F-null clocks, and every complete quadgram score/output hash. Inverse-plant three known message lengths per key and clock branch, checking exact expected text and the source score bar separately.",
    "parameters": "12 named streams (2 B1, 5 B4, 5 C2) × 56 targets × 2 signs × 2 Atbash settings × 2 F clocks = 5,376 manuscript cases. Key phase zero per page or for the joined stream. Three control messages × 96 setting branches = 288 complete-message controls. Source score bar >−5.2."
  },
  "dukotah-g3-pointer-framings": {
    "bucket": "method:direct-mapping",
    "procedure": "Map GP rune indices to prime value, one-based prime index or prime totient. Apply source modulo-32 base32 and decimal concatenation metrics, then compare 200 seed-3301+k histogram-preserving shuffles for every stream/metric. Replay original saved outputs and an independent low-entropy detector.",
    "parameters": "3 streams × 5 metrics × 200 source null calls = 3,000 source measurements, plus 15 real measurements and one planted low-entropy control."
  },
  "dukotah-grid-as-key-campaign7": {
    "bucket": "method:repeating-key",
    "procedure": "Replay three pinned Campaign VII scripts and independently reconstruct 33 named streams, mod-29 repeating-key decode in both signs, optional Atbash and F-interruption, source quadgram scoring, base range checks and byte XOR forensics.",
    "parameters": "33 source-named streams × 56 targets × 2 signs × 2 Atbash states × 2 F-clock states = 14,784 score cases. Strict source threshold > −5.2. Eight 120-rune known-message controls."
  },
  "dukotah-grid-token-roles": {
    "bucket": "method:generated-key",
    "procedure": "Execute pinned source programs on their original bytes, then independently replay all fixed ciphertext and index operators on each of three byte witnesses. Check exact source saved outputs and constructed known-text positives.",
    "parameters": "Five byte targets × (256 single-byte XOR + 18 keyword XOR + 8 additive stream signs + one as-is) = 1,415 outputs per byte witness; four exact pointer readings per witness. Three witnesses give 4,245 + 12 outputs."
  },
  "dukotah-longkey-skip-beam": {
    "bucket": "method:repeating-key",
    "procedure": "Execute unmodified Campaign VII C1 source in a temporary copy, then reconstruct its 120-state beam independently for all 54 full-page settings. Plant two known-text lengths with and without collision-triggered key skips across every source key and offset, checking complete plaintext equality separately from the source score bar.",
    "parameters": "Three named source key texts × six longest source unsolved pages × offsets 0, floor(length/4), floor(length/2) = 54 searches. Beam width120; steps 1 or2 permitted unconditionally. 36 planted control decodes (3 texts × 3 offsets × 2 lengths × 2 mechanisms)."
  },
  "dukotah-payload-key-skip": {
    "bucket": "method:repeating-key",
    "procedure": "Run the original payload_skip.py from pinned commit f08b20b in a temporary copy. Separately reconstruct its 320-state, up-to-three-skips beam and quadgram score for every page setting, compare each full plaintext-index hash and score, and plant the documented LP2-56 85-rune reading under each payload/sign/Atbash branch.",
    "parameters": "Four payload byte streams × two signs × two Atbash flags × 55 nonempty pages = 880 whole-page cases; offset zero, source beam width 320, at most three skipped values per rune, source score screen >−5.5. The source repeats payload bytes enough to cover initial page length and zero-pads beyond that array."
  },
  "dukotah-word-boundary-key-clocks": {
    "bucket": "method:repeating-key",
    "procedure": "Replay source FH1 separator advances, FH3 punctuation resets and W1–W5 word-prime self-keys; compare all source winners; check a complete known reading and seven planted positives; rerun each entire branch on 49 pagewise rune shuffles.",
    "parameters": "55 unsolved rune-bearing pages; FH1 3 separator sets × 4 streams; FH3 4 resets × 3 streams; W1–W5 × 2 signs × 2 Atbash states. 2,420 page/settings outputs; 49 complete-grid shuffles seeded 3301."
  },
  "emerson-running-key": {
    "bucket": "method:running-key",
    "procedure": "For every no-wrap source offset, subtract source-letter values modulo 29 from each target's first 192 rune indices. Select the maximum English quadgram score on the first 96 runes and assess the next 96 at the same offset. Repeat the complete search on eight seeded letter shuffles. Plant a known LP1-06 reading with the same key at offset 3301 and search it blindly.",
    "parameters": "LP2-00, 31 and 54; 43,325 zero-based offsets per search; 96 selection plus 96 holdout runes; eight full-source shuffles with seeds 330100–330107; one fixed source, arithmetic direction, model and representation."
  },
  "eternalth-f-preserving-vigenere": {
    "bucket": "method:repeating-key",
    "procedure": "Independently reproduce both source + operators. Exhaustively enumerate the F-preserving operator image at each of 11 key slots and test complete page outputs for forbidden letters. Invert only the ordinary operator and score complete outputs against known readings and 199 whole-selection page shuffles.",
    "parameters": "Fixed AIRAUMFERAE key, phase zero; 55 pages × two source branches; 11×26 image enumeration; nine solved-reading controls; 199 whole-selection shuffles for the ordinary branch."
  },
  "f-interrupter-gap-direct-read": {
    "bucket": "method:direct-mapping",
    "procedure": "Take each consecutive F pair globally or within a page, compute position distance or intervening-rune count, and map the literal integer to a zero-based GP rune index or exact GP prime; preserve each unmapped value at its original position.",
    "parameters": "458 F runes; 457 joined-page gaps or 403 within-page gaps; two distance conventions × two literal value maps × two boundary policies = eight cases. A complete reading requires all gaps to map."
  },
  "feedback-opening-census": {
    "bucket": "method:feedback",
    "procedure": "Subtract feedback modulo 29; before the chosen lag use a repeated scalar primer, then an earlier ciphertext or plaintext value. Test continuous-page and per-word initialization. Compare each output's first twelve runes with nine fixed known-reading openings.",
    "parameters": "2 feedback sources × 16 lags × 29 scalar primers × 2 boundary rules = 1,856 configurations; 55 pages and nine opening cribs = 918,720 exact comparisons."
  },
  "gp-prime-plaintext-feedback": {
    "bucket": "method:feedback",
    "procedure": "Decode every whole page by either previous-plaintext-prime feedback or cumulative plaintext-prime-sum feedback; rank complete GP-to-Latin outputs under the pinned English quadgram model. Repeat the entire selection on 199 independently seeded within-page-shuffled corpora.",
    "parameters": "2 equations × 29 scalar seeds × 2 arithmetic signs × 55 pages = 6,380 observed candidates; 199 complete-grid shuffles, seeds 33017200–33017398. Page-local starts, one key advance per rune."
  },
  "grid-barcode-fixed-render": {
    "bucket": "method:payload",
    "procedure": "Scan each of four bit canvases under eight D4 rotations/reflections and two color polarities with zxing-cpp restricted to QR Code and Data Matrix; verify generated positives and scan fixed-seed bit shuffles.",
    "parameters": "Four canvases times 16 transforms = 64 original scans; eight shuffles per canvas times 16 transforms = 512 comparison scans; bit scale 8 pixels, white quiet zone four modules; zxing-cpp 3.1.1 with rotate, invert and downscale retries disabled."
  },
  "grid-direct-bytes": {
    "bucket": "method:payload",
    "procedure": "Enumerate row- or column-wise reading with both outer directions, both initial inner directions and constant or alternating inner directions. Repeat all sixteen routes for all ten-bit I/l stem masks; apply six fixed text or file-header screens at byte offset zero.",
    "parameters": "16 full-length routes times 1,024 stem masks = 16,384 byte streams, 256 bytes apiece; all other cells fixed, including 2S."
  },
  "grid-openpgp-literal": {
    "bucket": "method:payload",
    "procedure": "Enumerate 16 row/column routes and 1,024 stem masks; check complete RFC 4880 new-format tag-11 packet framing at offset zero with definite and partial lengths and literal body fields.",
    "parameters": "16,384 byte streams; each 256 bytes. Valid tag11 header CB; packet must consume entire stream. Two planted packet controls including partial-length encoding."
  },
  "grid-payload-prf-contested-masks": {
    "bucket": "method:generated-key",
    "procedure": "Run source planted controls, extend them across every generator/reduction pair, enumerate all 64 witness masks, decode 3,840 source-defined cases and compare with the preregistered English-score rule and 200 shuffled-head reference scores.",
    "parameters": "Six positions 25, 175, 182, 199, 215, 237 each take majority or decimal witness value; 15 PRFs × mod/rejection × signs ±1; skip-aware beam width 120, max three key skips, forward offset zero, no Atbash."
  },
  "grid-payload-prf-opening-cribs": {
    "bucket": "method:generated-key",
    "procedure": "Regenerate all four pinned B-05 source parts, normalize sign and source key-Atbash into effective keys, verify source case hashes, and exactly check key-skip path feasibility without beam pruning or language scoring.",
    "parameters": "70,680 source configurations, 59,948 distinct effective 1,597-symbol keys, up to three rejected draws between emitted runes, 55 page starts and nine 12-rune cribs. Source offsets, directions, signs, shifts and contested-byte variants are unchanged."
  },
  "grid-payload-prf-seed-corner": {
    "bucket": "method:generated-key",
    "procedure": "Run source planted controls; decode the fixed 32 keys; compare source English score against its declared threshold and 200 shuffled-head controls.",
    "parameters": "Two raw 256-byte payloads × four PRFs × two reductions × two signs; beam width 120, maximum three key skips, offset 0, forward, no Atbash."
  },
  "grid-payload-prf-source-grid": {
    "bucket": "method:generated-key",
    "procedure": "Replay the published B-05 Part 1 main grid, Part 1b constant shifts, Part 2a two-witness masks, and Part 2b one-byte variants with the source skip-aware beam and English score. Preserve all configurations; reuse scores only for identical effective decoder inputs. Check pinned source controls and full-stream follow-ups separately.",
    "parameters": "70,680 source head-screen calls: 40,320 main-grid, 3,480 constant-shift, 3,840 two-witness-mask and 23,040 one-byte-variant. First 400 runes; beam width 120; at most three key skips; fixed English score ≥ −5.5."
  },
  "grid-prefix-split-openings": {
    "bucket": "method:repeating-key",
    "procedure": "Partition tokens by leading digit 0–4, retaining suffix order. Map suffixes to base-60 digit values modulo 29 or ASCII byte values modulo 29; for group 4 also parse 17 individual hexadecimal nibbles. Use each as a repeating GP29 key under both signs at every phase. Compare first 12 output indices exactly with each fixed opening.",
    "parameters": "Channel lengths 60/58/65/56/17; 1,058 named mapping/phase/sign settings including 34 group-4 duplicate settings; 55 target pages; nine openings; 58,190 named page cases and 523,710 exact comparisons."
  },
  "grouped-key-advance-openings": {
    "bucket": "method:repeating-key",
    "procedure": "For group size g in 2..5, subtract K[(phase+floor((rune index+offset)/g)) mod k] modulo 29; test all key and boundary phases.",
    "parameters": "43 keys; four group sizes; 4,326 phase/offset settings; 55 pages; nine openings; 2,141,370 comparisons."
  },
  "historical-prime-and-ps-keys": {
    "bucket": "method:generated-key",
    "procedure": "For each stream, source rune-bearing segment and joined stream, decode with both arithmetic signs, Atbash on/off and F interruption on/off; rank using the pinned English quadgram model.",
    "parameters": "9 streams × 56 targets × 8 settings = 4,032 cases; 12,956 runes in 55 separate source segments; threshold score_norm > −5.2."
  },
  "known-key-reset-prefix-gate": {
    "bucket": "method:repeating-key",
    "procedure": "Verify the saved second-koan/phase 0/subtract full outputs against direct canonical-input equations, then compare each first Warning12 mismatch with the first possible word or line reset. Exclude only strict-before mismatches. Decode reset variants only on synthetic controls, never manuscript targets.",
    "parameters": "One fixed 13-rune second-koan key; phase 0; subtraction mod29; one fixed 12-rune Warning opening;55 nonempty pages; two deterministic reset gates; four synthetic boundary controls. All55 saved arrays/12,956 runes independently checked."
  },
  "layout-count-streams": {
    "bucket": "method:direct-mapping",
    "procedure": "Compute 594 line and 2,776 word counts; interpret each as n mod29 or (n−1) mod29, score canonical GP Latin labels page-locally or joined. Compare the best of eight scores with best-of-eight maxima in 256 shared within-page count shuffles. Plant decoded GP readings in synthetic count streams.",
    "parameters": "Eight declared readings; 256 shared shuffles seeded 33017125–33017380. Every arm clears the frozen 100-English-quadgram eligibility gate."
  },
  "leo-chain-key-alignment": {
    "bucket": "method:generated-key",
    "procedure": "Replay source-named numerical streams under 14 nonzero-change bijections, 300 offsets, signs ±1 and both doublet key clocks; compare all nine source maxima and planted controls; rerun full grid on 39 within-section shuffles of source-selected pages 54–55.",
    "parameters": "21 effectively eligible sequence entries, including duplicate prime/primeidx; 352,800 evaluated settings per section, 39 selected-section shuffles; 2 planted prime-chain controls."
  },
  "leo-chain-sequence-keys": {
    "bucket": "method:generated-key",
    "procedure": "Replay the named 24-sequence, 200-offset, two-sign grid on five source streams; retain three best rows per section and stream. Replay the source solved-text running-key arm. For each section, select the grid maximum and compare with the same selection on 99 rune-order shuffles. Gate on planted raw and chain prime-key streams first.",
    "parameters": "Source sequence rules from pinned tests4.py; GP29 and chain Z28/Z29; random.Random(330104/330105) planted controls and 330104 section shuffles; plus-one selected-grid tails."
  },
  "lp2-53-red-known-keys": {
    "bucket": "method:repeating-key",
    "procedure": "For each of the documented Welcome and second-koan key vectors, decode the red rune indices under every phase and both signs. Score canonical GP transliteration with the pinned English quadgram model. Compare the best of all 42 against best-of-42 scores for 999 seeded rune-order shuffles. Gate first on nine solved 51-rune readings, their 200 shuffles each, and nine planted two-key encipherments.",
    "parameters": "Two key lengths 8 and 13, 42 phase/sign settings; score threshold −5.5; 999 family-wise shuffled red controls; nine known-reading and nine planted controls."
  },
  "lp2-54-55-autokey-reset": {
    "bucket": "method:feedback",
    "procedure": "P_i=(C_i-previous_ciphertext) mod 29; update previous_ciphertext=C_i. Unselected F behaves normally. Score the compact output after selected Fs are removed. Selected F is emitted unchanged, excluded from scored output, and sets previous ciphertext to zero. Sum ordered equal-symbol pairs within residue columns divided by sum ordered pairs within those columns. Maximize across all masks and periods; exact ratio comparisons. Keep all six F positions fixed. Independently permute the remaining non-F ciphertext multiset, freshly copied each trial. Repeat the complete mask-and-period search for each trial. This conditions on F positions, rune counts and length; it is not an English-text model.",
    "parameters": "Initial ciphertext state 0; modulus 29; all 64 subsets of six F positions; all periods 2–30 inclusive; 1,856 configurations per input. 999 shuffles; random.Random seed 330154; upper tail with ties and (count+1)/1000. Threshold 0.05. Bonferroni correction for the two planned reset/skip variants."
  },
  "lp2-54-55-autokey-skip": {
    "bucket": "method:feedback",
    "procedure": "P_i=(C_i-previous_ciphertext) mod 29; update previous_ciphertext=C_i. Unselected F behaves normally. Score the compact output after selected Fs are removed. Selected F is emitted unchanged, excluded from scored output, and leaves previous non-interruption ciphertext unchanged. Sum ordered equal-symbol pairs within residue columns divided by sum ordered pairs within those columns. Maximize across all masks and periods; exact ratio comparisons. Keep all six F positions fixed. Independently permute the remaining non-F ciphertext multiset, freshly copied each trial. Repeat the complete mask-and-period search for each trial. This conditions on F positions, rune counts and length; it is not an English-text model.",
    "parameters": "Initial ciphertext state 0; modulus 29; all 64 subsets of six F positions; all periods 2–30 inclusive; 1,856 configurations per input. 999 shuffles; random.Random seed 330154; upper tail with ties and (count+1)/1000. Threshold 0.05. Bonferroni correction for the two planned reset/skip variants."
  },
  "lp2-54-header-dictionary": {
    "bucket": "method:feedback",
    "procedure": "For A, I and O first-rune cribs, decode all eight later runes under ciphertext feedback P[i]=C[i]-C[i-1] or plaintext feedback P[i]=C[i]-P[i-1], modulo 29. Look up the exact resulting eight-rune GP string in the pinned corpus, aliasing its alternate J rune to manuscript J. Apply the same six checks to all same-length visible pairs. Plant A MOUNTAIN with primer seven under both rules as a positive control.",
    "parameters": "Canonical zero-based 29-rune GP order; three first-rune cribs; two one-step feedback modes; no reset at the word break. Pinned 138,466-row corpus at revision 9c10cafce02e512840cc9e173127930594a56281."
  },
  "lp2-54-header-feedback": {
    "bucket": "method:feedback",
    "procedure": "For each primer 0–28, decrypt the entire stream by P0=C0-k modulo 29 and then either P_i=C_i-C_(i-1) or P_i=C_i-P_(i-1) modulo 29. Re-encrypt every output and independently verify every saved equation. Compare the six outputs whose first rune is A, I or O.",
    "parameters": "29 primers × 2 recurrences = 58 complete outputs of 232 runes; one continuous stream, no word or row reset; one-rune ciphertext or plaintext feedback; no adaptive key or candidate selection."
  },
  "lp2-fibonacci-openings": {
    "bucket": "method:running-key",
    "procedure": "Apply Fibonacci shifts F_0=0, F_1=1, F_(n+2)=F_(n+1)+F_n modulo 29, with both subtraction and addition. Compare the first 12 output indices with nine fixed known openings; retain full candidates.",
    "parameters": "Offsets 0–28 inclusive; two directions; independent page reset; one term per rune; no interruptions. 55 rune-bearing pages, 3190 candidates, 28710 comparisons."
  },
  "lp2-known-vigenere-keys": {
    "bucket": "method:repeating-key",
    "procedure": "Apply each known key with every phase, both addition and subtraction modulo 29. Compare the first 12 output indices against each of nine known-opening vectors. Retain complete candidates.",
    "parameters": "Two vectors of lengths 8 and 13; all 21 phases; two signs; 56 pages; 2352 candidates and 21168 exact comparisons. Reset per page. No interruptions."
  },
  "lp2-page-pair-alignment": {
    "bucket": "method:numeric",
    "procedure": "For every unordered page pair compute aligned sum and difference modulo29, measure output IoC, and compare the global maximum to 256 seeded shared page shuffles within page-length-delimited bands that preserve every compared-prefix histogram.",
    "parameters": "1,485 distinct pairs × 2 arithmetic operations = 2,970 outputs; 256 global-max null trials; seed 330129."
  },
  "lp2-page-pair-english": {
    "bucket": "method:numeric",
    "procedure": "Align every unordered page pair at rune zero to the shorter length. Compute A+B, A−B, and B−A modulo 29; score GP Latin labels with a fixed English quadgram model. Compare best eligible stream to 256 maxima of complete shared conditional-band page-shuffle searches.",
    "parameters": "1,485 pairs × three operations = 4,455 streams, of which 4,136 have ≥100 Latin quadgrams. Each of 256 controls uses Random(33017127+t). Three synthetic planted English outputs check exact arithmetic recovery and the scorer."
  },
  "lp2-panel-prime-openings": {
    "bucket": "method:repeating-key",
    "procedure": "Repeat the sixteen panel-derived primes in spiral order as modulo-29 shifts, with addition and subtraction, and compare first twelve output indices to nine fixed openings.",
    "parameters": "Offsets 0–15; two directions; independent page reset; one term per rune; no interruptions. 55 rune-bearing pages, 1760 cases and 15840 comparisons."
  },
  "lp2-prime-minus-one-openings": {
    "bucket": "method:running-key",
    "procedure": "Apply prime-minus-one shifts modulo 29, with both subtraction and addition. Compare the first 12 output indices with nine fixed known openings; retain full candidates.",
    "parameters": "Offsets 0–28 inclusive; two directions; independent page reset; one term per rune; no interruptions. 55 rune-bearing pages, 3190 candidates, 28710 comparisons."
  },
  "lp2-prime-openings": {
    "bucket": "method:running-key",
    "procedure": "Apply prime shifts modulo 29, with both subtraction and addition. Compare the first 12 output indices with nine fixed known openings; retain full candidates.",
    "parameters": "Offsets 0–28 inclusive; two directions; independent page reset; one term per rune; no interruptions. 55 rune-bearing pages, 3190 candidates, 28710 comparisons."
  },
  "lp2-shifted-page-pair-differences": {
    "bucket": "method:numeric",
    "procedure": "Exhaust all unordered page pairs and integer relative lags with>=120 overlap; direct difference modulo29; compare global maximum IoC to128 shared whole-page permutations.",
    "parameters": "1,326 pairs; 331,908 alignments (330,582 nonzero lags); minimum overlap 120; 128 nulls; seed 330120261024; no wrapping or reversal."
  },
  "lp2-shifted-page-pair-english": {
    "bucket": "method:numeric",
    "procedure": "Exhaust every eligible unordered pair and relative offset; score A+B, A-B and B-A modulo 29 with unchanged prior English scorer. Compare observed global best with 128 shared whole-page permutation search maxima.",
    "parameters": "1,326 pairs; 331,908 alignments; 995,724 streams, including 991,746 nonzero-offset streams and 3,978 baseline overlaps; at least 100 Latin quadgrams; fixed recognition gate -5.5; 128 null trials; seed 330120261025."
  },
  "lp2-totient-openings": {
    "bucket": "method:running-key",
    "procedure": "Apply consecutive-integer totient shifts phi(j+s+1) modulo 29, with phi(1)=1 and both subtraction and addition. Compare the first 12 output indices with nine fixed known openings; retain full candidates.",
    "parameters": "Offsets 0–28 inclusive; two directions; independent page reset; one term per rune; no interruptions. 55 rune-bearing pages, 3190 candidates, 28710 comparisons."
  },
  "multiplicative-ciphertext-autokey": {
    "bucket": "method:feedback",
    "procedure": "Apply the exact absorbing-zero invariant of c[i]=p[i]×c[i−1] mod 29; enumerate zero-to-nonzero within-page edges; verify a synthetic positive control.",
    "parameters": "Every within-page transition on LP2-00–55; arbitrary plaintext values and page-start seeds; no statistical threshold required."
  },
  "mutated-dictionary-key-openings": {
    "bucket": "method:repeating-key",
    "procedure": "For each of 43 source rune keys replace one rune position or every instance of one rune type with each of the other 28 GP runes; deduplicate altered strings; test every phase in subtractive and additive repeating-key GP29 against nine fixed openings.",
    "parameters": "7,056 named rune-type changes + 8,652 named position changes = 9,856 distinct altered keys; 83,328 phases; 55 page starts; nine openings; two directions."
  },
  "pgp-packet-keys": {
    "bucket": "method:repeating-key",
    "procedure": "Extract the two v4 RSA public packet bodies and their binary fingerprints from the pinned Cicada key, map every byte modulo 29, try every cyclic phase and both additive signs, score complete pages using the fixed English quadgram model and 199 full-search page-shuffled nulls.",
    "parameters": "Four streams of 525,20,525,20 bytes; 2,180 phase/sign combinations per page ×55 pages =119,900 complete-page settings."
  },
  "prime-lag-autokey-openings": {
    "bucket": "method:feedback",
    "procedure": "One rune repeated for consumed j<lag; afterwards subtract prior cipher at lag or recovered plaintext at lag. No interruptions; reset each page.",
    "parameters": "11 prime lags 2..31; 2 feedback modes; 29 repeated single-rune primers; 638 settings; 55 nonempty pages; 9 frozen 12-rune cribs; 638 full 64-rune plants."
  },
  "public-kdf-seed-stretch": {
    "bucket": "method:generated-key",
    "procedure": "Run the pinned K1 expander control and the K2 planted-PBKDF2 control, then sweep the complete Stage A grid against LP2 with skip-aware beam width 400 and at most three key skips per rune.",
    "parameters": "534 ordered secrets × 27 KDFs × 3 salts × 2 reductions × 2 signs × 2 Atbash choices × 2 key directions = 692,064 LP2 decodes. Offset zero, first 120 runes. The K2 control independently traverses the same configuration grid on a planted message."
  },
  "public-multihistory-feedback": {
    "bucket": "method:feedback",
    "procedure": "For each stream, sweep seven fixed feedback functions, k=2..6, three history sources, both signs and both directions; score decoded transliteration using the pinned English quadgram table and 29 all-equal seeds for plaintext/mixed history.",
    "parameters": "56 streams x 7 functions x 5 history lengths x 3 sources x 2 signs x 2 directions = 23,520 scored configurations. Ciphertext history ignores the seed after k; plaintext/mixed source probe eq0 through eq28. Twenty-one k=3 planted controls."
  },
  "public-prng-seed-sweep": {
    "bucket": "method:generated-key",
    "procedure": "Run the source's seven generators for each of its 1,877 fixed seeds; decode both signs and both directions with its beam width 400 and maximum three rejected symbols; compare scores to the fixed −5.5 bar and 200 shuffled-prefix nulls.",
    "parameters": "Seven implementations × 1,877 seeds × 2 signs × 2 directions = 52,556 decodes; modulo-29 reduction, key offset zero, 120-rune screen."
  },
  "public-rsa-payload-e01": {
    "bucket": "method:public-key",
    "procedure": "Replay pinned E-01 public exponentiation and PKCS#1 v1.5 signature/encryption plus PSS padding checks on valid endian/alignment representations, exponents 65537, 3 and 17.",
    "parameters": "3 payloads; 2 usable PGP moduli; 3 valid encodings per PGP modulus; 3 exponents; 3 structural predicates = 162 evaluated matcher rows. Twelve source encodings excluded for s≥n, including every 2013-modulus case."
  },
  "public-wordlist-vigenere": {
    "bucket": "method:repeating-key",
    "procedure": "Subtract each source key modulo 29 at page phase zero; compare nine fixed 12-rune openings on LP2-00–55; separately verify complete Latin rune-label streams for all 58 archived pages.",
    "parameters": "43 archived keys, 58 complete source pages (56 unsolved-page opening-test pages), nine 12-rune openings, 21,285 exact opening comparisons."
  },
  "py27-prior-front-opening-cribs": {
    "bucket": "method:generated-key",
    "procedure": "Rebuild the source's exact 45,975-word ordered priority front. For each word, generate all four source Python 2.7 reducer and ABI key prefixes. Test exact existential keyskip1 paths against fixed page-start openings, with no beam pruning or English score.",
    "parameters": "45,975 priority words × grb5_mod_i386, grb5_rej_i386, shuffle29_i386, random29_amd64 = 183,900 generated cases; source sign -1, no Atbash, zero offset, up to three collision-rejected key draws per rune; nine openings and 55 page starts."
  },
  "r18-drift-ladder-replay": {
    "bucket": "method:repeating-key",
    "procedure": "Run F0 parity gate, replay the three-page planted offset control, and search 230 source-mined key candidates at 5,961 offsets each over first 100 runes of every nonempty page; compare all candidate rows with pinned source output.",
    "parameters": "Suppression 0.8129; beam width 400; maximum three skipped draws; predicted key offset start+rho*start with +/-4 standard deviations, plus uncorrected and restart controls; English-score gate -5.5."
  },
  "r26-derived-generators-opening-cribs": {
    "bucket": "method:generated-key",
    "procedure": "Regenerate each R26-A source keystream from the exact ordered dictionary and dense baseline. Check existential fixed-plaintext skip paths under exact and pair source presets, sign -1, no Atbash. No English scoring or beam pruning.",
    "parameters": "312 dictionary integer seeds plus 400 dense integers for eight Perl reductions and four TeX generators; 347 dictionary entries plus 400 dense integers for three Python 2.7 reducers at 64-bit wordsize and offsets 0,1,2,3,5,7,13. Each generated case gets exact/keyskip1 and pair/keyskip2 preset. 24,231 generated cases (19,986 distinct first-100-symbol streams); 48,462 rows; 55 nonempty page starts in LP2-00–55; nine cribs."
  },
  "relikd-autokey-interrupt-database": {
    "bucket": "method:feedback",
    "procedure": "Audit eight committed database files, recomputing every row's first-16-interruption cutoff, selected deletion, primer-dependent plaintext feedback and normalized whole-prefix coincidence score. Independently reconstruct eight complete known-text controls and map scored positions to page records.",
    "parameters": "GP29 prime/index previous-plaintext feedback × plus/minus sign × original/inverted input; primer field 0..28 with source field0-to-primer1 behavior; 2,412 saved rows, eight 96-rune controls with three declared inserted interruptions."
  },
  "relikd-interrupt-db-keyfit": {
    "bucket": "method:repeating-key",
    "procedure": "Extract the otherwise unreachable source break_cipher saved-row branch. For each row, delete its declared F occurrences before the twenty-first F from the fit prefix, fit both original source key models, and decode the complete section with source skip-clock semantics. Independently recount fits and decoded hashes.",
    "parameters": "Nine source database rows selected by interrupt F and score at least 0.55; two source fitters (18 outputs); source mean-similarity limits 0.05 and 0.04; six matched-length known-text controls plus solved-page and short skip-clock controls."
  },
  "relikd-rotated-key-source-gate": {
    "bucket": "method:repeating-key",
    "procedure": "Repair one integer-to-generator call using the source's shift_pattern helper; retain the nine sections, k3–18, step1..k−1, all phases, strict source IoC and similarity gates. Verify a 970-rune known reading and 49 shared whole-grid within-section shuffles.",
    "parameters": "1,936 key schedule settings per section; nine sections and 17,424 target settings; source IoC in (1.6,2.1), similarity <0.1; one complete known-text planted control and 49 complete-search shuffles."
  },
  "rotating-folded-key-openings": {
    "bucket": "method:repeating-key",
    "procedure": "Expand each key by left/right cycle rotation or forward/backward folding with/without repeated endpoints. Reduce to true period; test every phase; subtract scheduled key index modulo 29.",
    "parameters": "43 keys; four expansions; 6,272 settings; 55 pages; nine 12-rune openings; 3,104,640 comparisons."
  },
  "rsa-window-54-source-replay": {
    "bucket": "method:public-key",
    "procedure": "For starts 0–202, take 54 bytes in both directions; inspect each directly, then for exponents 65537, 3 and 17 inspect pow(value,e,2013 modulus) only when value is below the modulus. Apply the source’s strict/loose PKCS#1 v1.5 and PSS structural tiers.",
    "parameters": "3 payload readings × 203 windows × 2 directions = 1,218 direct inspections; 2,493 modular exponentiations after 1,161 s≥n exclusions. Ten planted type-1 and five planted PSS signatures; 200 random-buffer controls."
  },
  "rune-direct-byte-packing": {
    "bucket": "method:payload",
    "procedure": "Encode each target as high-bit-first five-bit index tokens, reversed-bit five-bit tokens, or single-byte GP primes. Append zero bits only at the end of each five-bit target. Screen whole-stream printable ASCII and strict UTF-8, and six exact file prefixes at byte offset zero.",
    "parameters": "55 nonempty pages plus one joined stream; three encodings; 168 streams. PNG, gzip, ZIP, PDF, ELF and MZ prefixes; no extra transformation."
  },
  "rune-direct-compression": {
    "bucket": "method:payload",
    "procedure": "Verify every reconstructed input SHA-256 against the earlier saved record; run complete-stream zlib, gzip, raw DEFLATE, bzip2 and XZ decoders at offset zero; require EOF, no unused input and output no larger than 1 MiB; independently rebuild bytes from page JSON.",
    "parameters": "168 input streams × five formats = 840 attempts; output cap 1,048,576 bytes; no offsets. Synthetic valid, truncated, trailing-junk and over-limit controls for all five formats, plus one rune-packed zlib fixture."
  },
  "section-1433-pairing": {
    "bucket": "method:numeric",
    "procedure": "Rebuild three 1,433-rune streams; test each pair under add/subtract modulo 29, forward/reverse second stream; choose highest whole-output IoC; repeat full 12-way selection for 999 seeded independent nonzero circular-shift trials.",
    "parameters": "Three pairings, four operations each, 1,433 positions, seed 14333301, 999 control trials; ties count as at least observed."
  },
  "section-1814-pairing": {
    "bucket": "method:numeric",
    "procedure": "Pair the two 1,814-rune streams in printed order. Apply B+A or B-A modulo 29, with B forward or reversed. Score the complete output by whole-stream IoC and select the best. Repeat this choice for all nonzero circular shifts of B.",
    "parameters": "Four operations; zero-based GP indices; 1,814 positions; 1,813 exhaustive nonzero circular-shift controls; ties count as meeting the observed best score."
  },
  "section-1894-pairing": {
    "bucket": "method:numeric",
    "procedure": "Pair the two 1,894-rune streams in printed order. Apply B+A or B-A modulo 29, with B forward or reversed. Score the complete output by whole-stream IoC and select the best. Repeat this choice for all nonzero circular shifts of B.",
    "parameters": "Four operations; zero-based GP indices; 1,894 positions; 1,893 exhaustive nonzero circular-shift controls; ties count as meeting the observed best score."
  },
  "solved-reading-running-key": {
    "bucket": "method:running-key",
    "procedure": "At every fitting contiguous source offset, add or subtract one key index per rune modulo 29 and score the entire page with the pinned English quadgram model. Compare the global best to 16 whole-key shuffled full-grid maxima. A separate post-observation diagnostic searches four disjoint 2,892-GP-rune windows of preserved Emerson English.",
    "parameters": "55 complete pages; 292,318 observed page/offset/sign alignments, 16 complete shuffled-key grids (seeds 33017100–33017115), both arithmetic signs, four post-observation English GP-key windows."
  },
  "spiral-branches-paired-subtraction": {
    "bucket": "method:numeric",
    "procedure": "For each aligned position output (B_i − A_i) mod 29. Search direct, reverse Branches, reverse full 1,738-rune tail, Atbash Branches, and Atbash full tail. Score each complete output by whole-stream ordered equal-symbol pairs / N(N−1), N=2,883. Compare the selected maximum to every nonzero circular shift of B and 999 within-page non-F shuffles of B; repeat all five variants per control.",
    "parameters": "Five predeclared variants; 2,883 positions; 2,882 exhaustive shifts; 999 shuffles with random.Random seed 33012883. Include ties. Shift comparison (tail+1)/2883; shuffle estimate (tail+1)/1000. Threshold 0.05, considered separately for both controls."
  },
  "typed-seed-random-opening-cribs": {
    "bucket": "method:running-key",
    "procedure": "Execute the pinned source's seed literals, date loop and six Python Random stream modes; apply two decode signs and each of four source-defined first-two-F removal masks; compare fixed openings with strict no-skip key alignment.",
    "parameters": "1,284 typed seed entries × six modes × two signs = 15,408 source configs; four F masks each = 61,632 paths. Key length 260, zero offset; 55 page starts and nine 12-rune cribs."
  },
  "wholepage-known-vigenere-keys": {
    "bucket": "method:repeating-key",
    "procedure": "Decode every full page with the documented Welcome and second-koan keys under both signs and all phases. Score the complete canonical GP Latin transliteration with the pinned English quadgram model. Gate on nine archived 66-rune readings and nine planted encipherments. Compare the single maximum over all pages/settings with 199 full-search pagewise rune shuffles.",
    "parameters": "55 pages; two key lengths 8 and 13; 42 settings per page; 2,310 outputs; fixed −5.5 English-score threshold; 199 global-search shuffled controls."
  },
  "wholepage-public-wordlist": {
    "bucket": "method:repeating-key",
    "procedure": "Decode every complete rune-bearing page with all 43 pinned wordlist keys, all key phases and both additive/subtractive directions. Score canonical Latin output with pinned English quadgram model; compare the single best output with 199 full-grid within-page shuffle maxima.",
    "parameters": "43 keys; 618 key-phase-direction settings; 55 pages; 33,990 full-page scores; nine genuine and nine planted controls; 199 global-null replicates."
  },
  "wulfic-advanced-running-keys": {
    "bucket": "method:running-key",
    "procedure": "Replay the source method-5 100-step offset/direction screen, ±100 one-direction refinement, word-plus-coincidence ranking; test four corpus plants on and off the sampling grid, one complete synthetic grid, and 49 whole-grid page shuffles.",
    "parameters": "18 pages × 4 source texts = 72 returned page/text candidates, each selected from its exact adaptive offset search; 49 full 72-candidate controls."
  },
  "wulfic-autokey-seed-families": {
    "bucket": "method:feedback",
    "procedure": "Replay six GP29 plaintext/ciphertext feedback recurrences for 22 source keyword seeds, every two-rune seed, every three-rune seed on source-eligible pages, and the one distinct four-rune P21–30 DEOR array. Preserve source gates, strict IoC threshold and page resets; compare 49 full-search shuffles.",
    "parameters": "4,488 named-keyword, 171,564 two-rune, 4,536,354 three-rune, and 60 distinct P21–30 DEOR settings; 49 within-page shuffled complete searches, seed 20261023."
  },
  "wulfic-cicada-byte-key-phases": {
    "bucket": "method:repeating-key",
    "procedure": "Read 25 pinned number/byte sources into modulo-29 and rejection-mapped key streams. For each of 50 keys and ten section alignments, score three arithmetic modes and all 29 shifts with the pinned phase-averaged stay/advance/skip HMM. Replay 200 planted positive/negative pairs with exact seed. Compare all serialized rows against the pinned Stage R tables.",
    "parameters": "50 mapped streams × 10 alignments × 3 modes × 29 shifts = 43,500 source settings; +30-nat pass line; uniform cyclic phase, transition 0.02/0.96/0.02, epsilon 0.1, pruning 1e−12. Control lengths 729 and 3316, fresh/next rekey, keep 0.19, RNG seed 3301."
  },
  "wulfic-crib-lfsr-recurrence": {
    "bucket": "method:generated-key",
    "procedure": "Replay the source's original crib-drag Berlekamp-Massey and IoC gate. Separately fit the first m-2 key symbols from each selected source crib, verify the last two, predict the next 128 runes and score only that continuation; rerun the complete page/crib/mode/offset selection on 199 shared seeded page shuffles.",
    "parameters": "Original 21 source cribs length>=4, 3 directions and 12 mapped pages; corrected 13 source cribs length>=6, 3 directions, recurrence order 2–5, all offsets leaving 128 runes, 11 LP2 pages; 199 shuffle trials seed 20261023."
  },
  "wulfic-grid-compression-source-replay": {
    "bucket": "method:payload",
    "procedure": "Replay the pinned Stage X4 component with 100,000 seeded uniform-byte calibration blocks for each decoder. Test each complete grid route with raw DEFLATE, zlib, gzip, bzip2 and LZMA; also preserve Stage N offset-zero signature rows. Independently reconstruct the grid and every decoder result.",
    "parameters": "Five source decoders × four routes = 20 complete-stream calls, plus four signature checks. One bounded call per decoder with 1 MiB output cap; source PASS requires EOF and empirical null rate ×20≤0.01."
  },
  "wulfic-grid-long-byte-sources": {
    "bucket": "method:generated-key",
    "procedure": "For each of six pinned source byte streams, all cyclic phases, row/row-reverse/column/column-reverse and XOR/grid-minus-key/grid-plus-key/key-minus-grid, count distinct values in the complete 256-byte output. Preserve source positive and negative gates and independently recompute all LP2 minima.",
    "parameters": "Six source streams; 16 route/operation cells each; 2,865,136 source-phase trials. D≤120 passes. Twenty-four source positives at their planted cells, 18 uniform-grid negatives, and negative mean D within 162.0±0.5 are required for a valid run."
  },
  "wulfic-grid-native-keys": {
    "bucket": "method:generated-key",
    "procedure": "Replay source Stage N all 456 rows, independently rebuild the grid from site export, repeat 72 byte transforms and 384 GP29 likelihood calculations, then run explicitly post-replay synthetic detector diagnostics.",
    "parameters": "12 finite byte keys×3 operations×2 directions=72; two GP29 grid encodings×2 directions×3 decode modes×(29 constant shifts+3 rune streams)=384; source thresholds 90% printable or listed signature, and log LR+30 nats."
  },
  "wulfic-keyword-lfsr": {
    "bucket": "method:generated-key",
    "procedure": "Replay the source keyword-seeded LFSR, strict normalized-IoC reporting gate, complete planted known-reading search, and 199 whole-grid page-shuffle controls.",
    "parameters": "400 source settings, 396 distinct manuscript decoded outputs, 199 complete page-shuffle searches."
  },
  "wulfic-keyword-ramp": {
    "bucket": "method:generated-key",
    "procedure": "Apply each source-assigned GP29 keyword with all nine called progressive steps; score with the source English-substring function. Check one full known-reading plant and 199 shared page shuffles of the entire 90-case grid.",
    "parameters": "10 pages × 9 source steps = 90 candidate outputs; 199 complete shared page-shuffle searches, seed 20261023."
  },
  "wulfic-lfsr-singleton-constraints": {
    "bucket": "method:generated-key",
    "procedure": "Exhaust feedback tap tuples over GF(29), solve invertible first-L singleton constraints for all I/A assignments, test remaining singletons and decode example full pages exactly; independent small-grid oracle and planted controls.",
    "parameters": "L=1..5; each coefficient 0..28; plaintext I=10 or A=24 at visible one-rune words; sub/add/Beaufort directions; first-L invertible systems only; 29^L tuples per length and target."
  },
  "wulfic-liber-al-offset-sweep": {
    "bucket": "method:running-key",
    "procedure": "Run the source's complete 102-row coarse search, take its six best tuple-sorted rows, examine both modes within ±200 of those offsets, keep duplicate coarse/refined rows and source top 100. Repeat the complete selection on 199 shuffled-order pages; run sampled and off-grid planted controls.",
    "parameters": "Source offsets 0..5,000 in steps of 100 followed by source-selected ±200 neighborhoods; Beaufort and subtract modes; source weighted six-trigram score and IoC secondary ordering; shuffle seed 20261023."
  },
  "wulfic-native-key-streams": {
    "bucket": "method:running-key",
    "procedure": "Replay pinned Stage I and M complete candidate grids, then measure a separately identified post-replay planted-key diagnostic within each finite key's usable length.",
    "parameters": "Three Stage I keys × 10 alignments and three Stage M keys × 12 alignments; all three sub/add/Beaufort directions and 29 shifts; start at zero; source reading threshold log LR >=30. Supplemental 20 planted and 20 wrong-key draws per stream."
  },
  "wulfic-number-key-streams": {
    "bucket": "method:generated-key",
    "procedure": "Replay Wulfic Stages AG and AH, validate all source candidate/control tables byte-for-byte, and independently check the parameter grid, page stream, arithmetic prefixes and duplicate stream.",
    "parameters": "10 AG names and 12 AH names (21 distinct streams); nine separate sections plus one continuous stream; sub/add/Beaufort; 29 shifts; 1,000 uniform start positions; score pass >=30, cell exclusion <=-10 for all shifts after controls pass."
  },
  "wulfic-p08-hint-grid-keys": {
    "bucket": "method:repeating-key",
    "procedure": "Verify source-grid rows against the 140-byte LP1-08 payload; correct the legacy page path, replay seven unrotated keys and five keys at all rotations in three GP29 modes using the source IoC/singleton gates; encrypt known LP1 readings as positive controls; shuffle each source page 199 times and repeat the whole phase sweep.",
    "parameters": "47 pages; 987 fixed and 17,766 rotated-key cases; 510 planted transforms; source fixed IoC>1.3 or IoC>1.15 with singletons I/A, rotated IoC>1.25; 199 shared page shuffles. A later LP2-only readout uses the same random stream."
  },
  "wulfic-periodic-word-crib-votes": {
    "bucket": "method:repeating-key",
    "procedure": "Replay original word-vote keys and source stdout on the two example page/period pairs. Separately train on alternating visible word slots, score exact dictionary words on untouched slots, run 12 planted known-message folds and 199 matched whole-selection shuffles.",
    "parameters": "Source periods 43 and 17; SUB, ADD, BEAUFORT; visible 2–15-rune words; source-insertion-order vote ties; two train/holdout folds; 199 shuffles seeded 33014317."
  },
  "wulfic-prime-keyword-stream-families": {
    "bucket": "method:generated-key",
    "procedure": "Replay three archived finite searches as one shared batch: source keywords, source prime generators and F-skip, and keyword-stepped prime streams. Preserve each source screen and compare branch maxima against 49 full-search within-page shuffles.",
    "parameters": "540 repeating-keyword settings on ten pages; 11,880 prime-stream settings on eight pages; 5,285,280 stepped-keyword settings on eleven pages; three arithmetic directions; 49 seeded complete-search controls, seed 20261023."
  },
  "wulfic-square-title-vocabulary": {
    "bucket": "method:generated-key",
    "procedure": "Run only the pinned Stage I title function; independently derive all five 16-value sequences, compare the constructed cell-value set with the printed panel and recalculate all 30 two-word outputs from Liberpedia page text.",
    "parameters": "Five declared sequences x outward/inward x ciphertext-key, ciphertext+key and key-ciphertext, modulo 29; first nine key values; complete two-word vocabulary gate; 20,000 seeded random-key controls."
  },
  "wulfic-structural-pip-ps-normalized": {
    "bucket": "method:running-key",
    "procedure": "Generate the source PIP stream and three P.S.-number encodings, apply all eligible source offsets and three decode directions, require all one-rune words to be I/A, then screen by 29×raw IoC >1.3. Repeat the complete selected-max search on 199 page shuffles.",
    "parameters": "Million-limit source sieve; PIP n bound 50,000 and offsets 0–999; P.S. digit/pair/base29 encodings and offsets 0–49 subject to source length check; sub/add/Beaufort. Source page ordinals 21–54 map to LP2-04–37. No 7×7 key execution."
  },
  "wulfic-systematic-stream-source": {
    "bucket": "method:generated-key",
    "procedure": "Run every entry of the source's 26-stream dictionary in three modes over every eligible source page. Run all 29^4 ordered two-value LFSR state/tap tuples in three modes over the three highest-singleton pages, including zero/singular tap cases. Preserve the source IoC, bigram and I/A singleton score and hit thresholds. Repeat the entire selected grids on 19 within-page rune shuffles.",
    "parameters": "2,964 stream page-settings; 6,365,529 LFSR page-settings; source thresholds combined>2 or IoC>1.5 for streams, combined>3 for LFSR; shuffle seed 20261023."
  }
} );
 function classification(record){
  const entry=REVIEWED[record?.id];
  if(!entry||record.scope?.procedure!==entry.procedure||record.scope?.parameters!==entry.parameters)return null;
  return Object.freeze({bucket:entry.bucket,label:LABELS[entry.bucket],basis:'reviewed procedure and parameters'});
 }
 function project(source){
  const data=structuredClone(source),view=data.views?.all;if(!view||!Array.isArray(view.nodes))throw Error('Build the complete research navigation before projecting methods.');
  const nodes=new Map(view.nodes.map(n=>[n.id,n]));if(nodes.size!==view.nodes.length)throw Error('Repeated navigation identity.');
  const solve=nodes.get('solve-lp2');if(!solve)throw Error('The solving area is missing.');
  const families=['method:running-key','method:generated-key','method:numeric','method:repeating-key','method:feedback','method:payload'],affected=new Set(families.flatMap(id=>nodes.get(id)?.members||[])),aliases={...(data.method_navigation?.aliases||{})},diagnostics=[];
  function add(id,label){if(nodes.has(id))return;const n={id,parent:solve.id,label,color:solve.color,kind:'method',record_id:null,children:[],members:[],parent_basis:'reviewed method navigation',description:DESCRIPTIONS[id]};nodes.set(id,n);view.nodes.push(n);solve.children.push(id);}
  add('method:direct-mapping',LABELS['method:direct-mapping']);add('method:public-key',LABELS['method:public-key']);
  for(const [id,label]of Object.entries(LABELS)){const n=nodes.get(id);if(n){n.technical_label=n.technical_label||n.label;n.label=label;n.description=DESCRIPTIONS[id];n.parent_basis='reviewed method navigation';}}
  function ancestor(id,wanted){let n=nodes.get(id),seen=new Set();while(n){if(n.id===wanted)return true;if(seen.has(n.id))throw Error('Cyclic navigation.');seen.add(n.id);n=nodes.get(n.parent);}return false;}
  // Chain-increment decoding is an actual arithmetic operation, unlike the generator-source groups.
  const keepGenerated=new Set(['method:generated-key/operation/9061cfb91b2d84c8','method:payload/operation/10cdcb6574e9d873']);
  for(const [id,parentId]of [['method:payload/operation/10cdcb6574e9d873','method:generated-key'],['method:payload/operation/3d8d5e5146876c3d','method:public-key']]){const group=nodes.get(id);if(group){const parent=nodes.get(group.parent);parent.children=parent.children.filter(child=>child!==id);group.parent=parentId;group.parent_basis='reviewed method navigation';nodes.get(parentId).children.push(id);}}

  for(const rid of affected){
   const record=data.records[rid],leaf=[...nodes.values()].find(n=>n.record_id===rid);if(!record||!leaf)throw Error('Missing classified research record.');
   let bucket=classification(record)?.bucket;
   if(!bucket){diagnostics.push({recordId:rid,reason:REVIEWED[rid]?'reviewed-text-changed':'method-not-reviewed'});if(ancestor(leaf.id,'method:generated-key')||ancestor(leaf.id,'method:running-key'))bucket='method:generated-key';else {add('method:other-decoding','Other decoding rules');bucket='method:other-decoding';}}
   const generatedGroup=nodes.get(leaf.parent),keep=ancestor(leaf.id,bucket)&&(bucket!=='method:generated-key'||generatedGroup&&keepGenerated.has(generatedGroup.id));
   if(!keep){const previous=nodes.get(leaf.parent);if(previous)previous.children=previous.children.filter(id=>id!==leaf.id);leaf.parent=bucket;leaf.parent_basis='reviewed method navigation';nodes.get(bucket).children.push(leaf.id);}
  }
  // Drop emptied source/parameter group shells; retain aliases for old deep links.
  let changed=true;while(changed){changed=false;for(const n of [...nodes.values()])if(!n.record_id&&n.id!=='all-research'&&!n.children.length&&!Object.hasOwn(LABELS,n.id)&&n.id!=='method:other-decoding'){
   let parent=nodes.get(n.parent);if(!parent)continue;
   if(!families.some(id=>n.id.startsWith(id+'/')))continue;
   let target=parent;while(target&&!Object.hasOwn(LABELS,target.id)&&target.id!=='method:other-decoding')target=nodes.get(target.parent);
   const destinations=[...new Set(n.members.map(rid=>classification(data.records[rid])?.bucket).filter(Boolean))];aliases[n.id]=destinations.length===1?destinations[0]:destinations.length>1?'solve-lp2':target?.id||'solve-lp2';parent.children=parent.children.filter(id=>id!==n.id);nodes.delete(n.id);changed=true;
  }}
  // All kept subtrees still have one record leaf; recompute exact members and inherited colour.
  const visited=new Set(),records=new Set(),walking=new Set();
  function visit(id,color){const n=nodes.get(id);if(!n||walking.has(id)||visited.has(id))throw Error('Invalid navigation tree.');walking.add(id);visited.add(id);if(color)n.color=color;
   if(n.record_id){if(n.children.length||records.has(n.record_id)||!data.records[n.record_id])throw Error('Repeated or missing record.');records.add(n.record_id);n.members=[n.record_id];}
   else {n.members=[];for(const child of n.children){const c=nodes.get(child);if(!c||c.parent!==id)throw Error('Inconsistent navigation parent.');n.members.push(...visit(child,n.kind==='aim'?null:n.color));}}
   walking.delete(id);return n.members;
  }
  visit(view.root);if(visited.size!==nodes.size||records.size!==Object.keys(data.records).length)throw Error('The projection must retain every research record exactly once.');
  view.nodes=view.nodes.filter(n=>nodes.has(n.id));
  data.method_navigation={schema:'liberpedia-research-method-navigation-v1',aliases,diagnostics};return data;
 }
 const api=Object.freeze({project,classification,LABELS,DESCRIPTIONS,REVIEWED});if(typeof module==='object'&&module.exports)module.exports=api;else root.ResearchMethodNavigation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
