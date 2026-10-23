# Beam prefix-sharing prototype (internal)

This directory tests a representation-only optimization of the pinned B04 decoder at Dukotah revision `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`, source SHA-256 `74c47d170a9cb1966ff78d7448f6081dfab3bcc928f032603add3f76dae2e1ff`. It does not change the source, its score model, the search grid, or any published runner.

The source copies the entire transliteration and plaintext-index list for each new beam child. `beam_shared.py` keeps only the final three Latin letters needed to score any newly completed quadgram, plus a parent-linked rune node. It reconstructs the winning text and rune list once. Multi-letter rune transliterations are scored letter by letter in the same order; the per-child quadgram delta is accumulated before adding it to the parent score, preserving floating-point grouping. Candidate enumeration, skipped-key reads, stable score sort, beam cutoff, first-key read, worst-case zero-padding branch and final `Q.score_norm` are otherwise the source operations.

`fixture-plan.json` and `matrix.json` were frozen before comparison. `validate.py` tests 45 short cases spanning random and English-derived text, lengths 1–400, signs, offsets, Atbash, key-shortfall padding, zero/constant tie cases, beam widths and skip limits. It also tests one 12,956-rune source-equivalent input. All five returned fields match exactly, including floating-point scores; an `ObservedKey` wrapper records identical key reads and padding behavior. On the full case, both implementations made **36,109,480** key reads, saw the same highest index (13,268), took the zero-extension branch once and read no extended zeros. The paths and transliterations also match exactly. See `short-receipt.json` and `full-receipt.json`.

After parity passed, `bench.py` timed native-list inputs with serial paired calls and identical outputs:

| Length | Repeats | Source median | Prototype median | Ratio |
|---:|---:|---:|---:|---:|
| 120 | 30 | 2.437 ms | 1.954 ms | 1.25× |
| 400 | 5 | 196.045 ms | 135.383 ms | 1.45× |
| 12,956 | 1 | 95.991 s | 12.680 s | 7.57× |

This is one Windows host and one full-length text/key case, so the 7.57× ratio is a measured prototype result, not a throughput guarantee for every B04 setting. The 120-rune case has much less prefix-copy cost; the gain grows with length. Nothing here justifies replacing an official search runner without a separately frozen integration test over its real candidate/key-padding interface and chunk/checkpoint outputs.

From the repository root, reproduce with `python research/performance/beam-prefix-sharing-2026-10-23/validate.py --verify` and `python research/performance/beam-prefix-sharing-2026-10-23/validate.py --verify --full`. Running `bench.py` remeasures host-specific timings and replaces `benchmark.json`.

## Actual LP2 Stage D addendum

`stage-d-plan.json` was frozen before these two comparisons. It pins the full 12,956-rune joined LP2 input, the top Stage A reverse-key row and top Stage B forward-key row, their saved source receipts, and the **native Stage D key rule** (`len(cipher) + offset + 512` requested before whole-key reversal, if selected). Both native keys and all input files are checked by SHA-256. The exact pre-option helper used for the original comparison is preserved at `../b04-stage-b-2026-10-23/resumable_d_pre_optional.py` (SHA-256 `f24dc1b9bd7afd030b2973786bb60e9f60ec0c710517c63a579900d10d780506`), so subsequent optional-runner edits do not alter this frozen receipt. This uses the pinned external Dukotah checkout and the locally saved Stage A/B merged receipts; it is an internal workspace test, not a portable experiment bundle.

`stage_d_validate.py --pair` compared the complete returned dictionaries and observed key reads against the original source decoder. Both matched exactly, including the entire 12,956-rune decoded paths, transliterations, beam and normalized scores, final pointers, and key-read counts. The zero-extension branch ran once in each case but **no padded zero was read**. On this host the source/prototype elapsed times were 100.77/24.00 seconds for Stage A (4.20×) and 107.32/28.97 seconds for Stage B (3.70×). These are two representative full-input cases, not a measured throughput guarantee for the full campaign.

`stage_d_validate.py --memory` decoded the Stage A case in two fresh processes, polling RSS every 5 ms separately from the timing comparison. Source peak RSS was 176.2 MB (139.9 MB above its baseline); prototype peak was 50.6 MB (14.3 MB above baseline). A single sampled process pair does not establish an exact maximum or a general memory bound. Its outputs and key reads again agreed.

From the repository root, run `python research/performance/beam-prefix-sharing-2026-10-23/stage_d_check.py` for a fast read-only check of saved receipts and pinned dependencies. Re-running the long comparisons uses `python research/performance/beam-prefix-sharing-2026-10-23/stage_d_validate.py --pair` and `python research/performance/beam-prefix-sharing-2026-10-23/stage_d_validate.py --memory`; these overwrite their corresponding receipts with new timing and memory measurements. The pinned source and official Stage D runner remain unchanged. The full Stage D search and its checkpoint behavior were not evaluated here.

## Optional checkpoint-runner gate

The local `research/performance/b04-stage-b-2026-10-23/resumable_d.py` now accepts `--decoder-backend prefix_shared`; omitting it retains the original source decoder. The manifest binds the backend name, wrapper hash, optional prototype hash, pinned source hashes, input segments and ordered key picks. A checkpoint from one backend cannot be resumed with the other. The synthetic fixture plan was frozen before the runner edit (`optional-backend-fixture-plan.json` SHA-256 `7a4422c7f5163f53a8da2708e64f783d25bc695e822572bca0fe00f323eeafdd`). `test_optional_backend.py` compares all four complete synthetic cell rows, key-read audits and summary fields; also checks a stable tie, real zero reads from short-key padding, four-worker execution, partial resume and tamper/cross-backend refusal. All pass. The tiny four-cell synthetic run is dominated by worker startup, so its per-backend elapsed values in `optional-backend-test-receipt.json` are descriptive rather than an acceleration measure. Actual LP2 Stage D remains unrun.
