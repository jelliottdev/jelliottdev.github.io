# Shifted direct-English page arithmetic

This is a fresh manuscript method grid extending the existing zero-offset English page-pair record, grouped in the same page-pair arithmetic family. It does not duplicate the prior shifted-IoC result: every output is scored for English under the exact existing model and unchanged original Numba scorer.

Before target scoring, a synthetic-only benchmark measured the reused three-arm scorer at 0.01069 seconds for 2,438 alignments, projecting a few minutes for the complete target and 128 null searches. The grid, model hashes, controls and shuffle seed were then frozen in `plan-frozen.json` and its SHA-256 receipt.

The frozen scientific manifest is bundled as `frozen-plan.json`. Its bytes and hash are unchanged from the pre-target intake copy and still match `results.json`'s `plan_sha256`. The filename distinguishes its portable bundle-relative input paths from the site's conventional repository-relative `plan.json` schema. Runtime and independent checks verify every manifest input hash; scientific plan contents and numerical results were not rewritten for packaging.

All 55 transcript inputs are the same as the earlier page-pair family. Fifty-two qualify for the 120-rune minimum overlap. The grid is 1,326 pairs, 331,908 alignments and 995,724 arithmetic streams: sum and both subtraction directions. Exactly 3,978 zero-offset streams overlap the old English record and match its scores; 991,746 shifted English streams extend the tested domain. They remain one method-family variant.

Three newly constructed random-key page pairs recover the known 184-rune Warning at nonzero offsets 1, 37 and −53. Complete pair searches select each exact reading with score −4.478376; shuffled second-page controls fall below −5.5. All controls ran before manuscript scoring.

The manuscript maximum is LP2-13 minus LP2-32 at relative shift 56, over 121 runes and 155 Latin quadgrams, score −6.4925927001. Zero streams reach −5.5. One hundred of 128 complete shuffled-page search maxima score at least as highly, yielding the global plus-one comparison 101/129 = 0.7829457364. This bounds only direct shifted arithmetic under the fixed English rule; it does not exclude general shared-key encryption.

The independent checker uses the prior separately written one-stream scorer with a separate shifted enumerator. All 995,724 observed scores match exactly (maximum delta zero), as do all 3,978 baseline overlaps. It independently checks the complete planted and shuffled-control pair searches, all 128 null-winning slices and exceedance arithmetic. It does not independently exhaust all alignments of all null trials; the producer performed those complete searches and `run.py --check` regenerates them.

All four grouped family records pass schema/hash/article/family preflight. The readable 600×460 SVG uses 20px-or-larger labels and explicit actual/shuffled/known-reading semantics. No prior cohort files, shared data/build files or commits were changed.
