# D-04 remaining-page manuscript extension

The source and earlier published record cover 5,072 coefficient vectors, constants 0/1, both signs and offset zero on LP2-00/05/20. This follow-up excludes those pages and executes the same full-page rule on the other 52 nonempty LP2 pages: 1,054,976 new settings, grouped as one family variant.

`plan-frozen.json` and its SHA-256 were written before target scoring. Its bytes are identical to the portable draft `frozen-plan.json`; all original source hashes, target arrays and control rules are retained. Original MIT source and license are bundled.

The acceleration is confined to constant seed keys. All admitted beam paths emit the same plaintext rune at a given ciphertext position; only the tied key pointers differ. The initial-k zero-feedback convention, output transliteration and original English score remain exact. First, 52 native-source cases (48 deterministic random and four repeat-heavy cases) matched plaintext and scores exactly. The source coefficient-list crosswalk also matched all 5,072 vectors. Source checks added afterward span the first/last vector at every history depth and the exact known-reading rules, with zero score differences.

Both matched full 20,288-setting known-Warning searches select their true rule at rank one and recover all 184 runes. Scores are −4.478376; wrong unit-coefficient comparisons are −7.714165 and −7.430221. They do not measure recovery from key skips: a constant seed makes those skips unobservable.

The synthetic complete-page benchmark was 0.03496 seconds, projecting about 60 seconds for the 52-page target and 32 complete null searches. Actual target execution took 2.252564 seconds and all null searches took 75.057711 seconds, excluding compilation, source parity and controls. No setting reaches the source −5.2 line. LP2-49 gives the maximum −6.1758458861 with depth3, coefficients 9/23/27, seed1 and subtraction. Fifteen of 32 whole-search null maxima meet or exceed it: plus-one comparison 16/33.

The independent checker reconstructs every observed score using separate feedback/scoring loops and original source coefficient/scorer objects. All 1,054,976 scores match exactly; it checks full known-reading searches, additional native-source cases, source/site page identity and all 32 null-winning cases. It does not independently exhaust every setting in each null trial; the producer does.

The requested `run.py --check` was executed successfully. It regenerates source parity, both full known-reading searches, the whole target and all 32 full null searches, then compares every deterministic scientific field and every score value. It ignores only four named timing fields and does not rewrite expected outputs. The original scientific result and score bytes remain unchanged. Hash, frozen-plan, plot and XML checks pass.

The ready draft is `experiments/records/d04-remaining-page-feedback`. The only publication dependency at handoff is root adding identical family metadata to its existing baseline record; this agent did not modify shared baseline/data/build files or create a commit. No prior cohort was edited.
