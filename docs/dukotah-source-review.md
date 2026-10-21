# Dukotah repository: experiment leads and evidence boundaries

Source reviewed at commit `f08b20b632d91209ddbaa747e8e2f23df0c78ba1`, not a moving branch. The complete Git tree lists 4,388 entries; the central ledger contains 172 entries. This was a targeted source/code review, not execution of the repository's experiments or an audit of every file. Downloaded-source SHA-256 hashes are recorded in `dukotah-source-manifest.json`.

## Highest-value additions

| Proposed family or variant | Concrete test | Existing Liberpedia overlap | Evidence needed before publication |
| --- | --- | --- | --- |
| Language sensitivity of candidate scoring | Give a fixed scoring system correctly decoded texts in each language; measure exact rune recovery separately from whether its score accepts the text. Include wrong-key and shuffled controls. | Language comparison family and candidate-reading guide. New scorer calibration, not another word-length ranking. | Pin the scoring model and training text, translation-to-rune rules, passage selection, lengths, thresholds and all controls. Use aligned held-out passages where possible; report every language equally. |
| Decoder sensitivity to repeated-symbol suppression | Plant known plaintext under specified key-skipping and value-rewriting rules; compare rigid and skip-aware recovery with the correct and wrong keys. | Uniform-additive doublet test and F-interrupter autokey variants, but their models are different. | Specify the encoder first, including skip timing, signs, resets and fallback behavior. Freeze decoder width and skip limits. Report exact index recovery and scores separately. |
| Search-size calibration | Run a declared bounded wrong-key search on planted and null data, retaining the maximum score for each complete search. | Candidate-reading acceptance rules and search-space guide. | Calibrate the whole selection procedure, including adaptive choices and correlated keys; do not use an independent-Gaussian maximum formula as a universal threshold. |
| Short-seed versus external-pad controls | Plant a reproducible short-seed stream and test a fixed seed dictionary that includes its source seed; include omitted-seed and wrong-key controls. | Keystream experiments, but a separate derivation family and bounded seed coverage are needed. | Pin generator, seed encoding, counter endianness, output reduction and skip rule. A random-looking ciphertext does not prove a one-time pad. |
| Image-based transcription checks | Reproduce template/segmentation comparisons and test deliberately inserted missing, extra and swapped glyphs, including ornate initials and full-line omissions. | Transcription-checking guide and image audits. | Separate image-independent segmentation from alignment supplied by the existing transcription. A method using canon's line inventory cannot independently discover a line absent from that inventory. |

The first priority is scorer calibration: it directly complements the current eight-language work and tests a different failure mode. The second is a small, controlled encoder/decoder benchmark before any manuscript sweep. The scorer-only subset is now reproduced in [English scorer controls](../experiments/records/english-scorer-controls/article.md), with independently checked results. The planted-decoder, search-size, seed and transcription proposals remain unexecuted leads.

## Sources inspected

- [Paper](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/PAPER.md): revisions to earlier conclusions, language/scorer controls, decoder model limitations, and references to underlying reports.
- [Central ledger](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/LEDGER.json): measured, negative, incomplete, unrun and superseded entries must remain distinct. A ledger label is not independent verification.
- [Scorer-language script](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L7-redteam/a1_scorer_language.py): separates rune recovery from an English score; depends on additional corpus, conversion and decoder modules. Its input loader uses `errors="ignore"`, and its prose loader trims the outer eighths of long files. Fresh work should preserve byte/decoding diagnostics and explicit passage boundaries rather than silently inherit these choices.
- [Scorer implementation](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/src/lp/score.py): English quadgram model, unseen-quadgram floor and ASCII A–Z filtering. Those preprocessing choices matter for other languages and transliterations.
- [Benchmark account](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/benchmark/README.md), `plant.py` and `gates.py`: useful encoder/decoder control structure; no local execution claimed.
- [Older solver summary](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/docs/FINDINGS-FOR-SOLVERS.md): contains broad elimination and external-pad language that conflicts with the newer paper and ledger. Do not use it as a definitive exclusion list.

## Claims not imported

Near-uniform frequencies, high entropy and unsuccessful bounded searches do not establish that the intended cipher uses a full-length independent pad. A finite battery failing to distinguish two constructions establishes only the observed behavior under that battery. The repository itself retracts the unconditional unsolvability verdict, but its remaining “OTP-class” framing still needs explicit model and identification limits.

Likewise, reproducing known solved pages validates those implementations and controls; it does not validate every unrelated search mechanism or every negative claim. Recovery power must be checked for the specific encoder, decoder, scoring model, language, sample size and search budget.

For transcription work, distinguish correct rune identity, segmentation, line completeness and independent provenance. The paper discloses residual ornate-initial and whole-line limitations. Do not replace Liberpedia's existing evidence boundaries with the broader shorthand that the transcription is simply closed.

## Integration rule

Group related encoder variants in one family and record exactly which assumptions changed. Keep source-reported outcomes as leads until freshly reproduced with pinned inputs and an independent check. Any final article should include a clear model diagram and a complete control table, with equal treatment of the languages. No hosted AI calls or large seed sweeps are necessary for this initial review.

## Planted decoder follow-up

The [decoder protocol](../experiments/plans/decoder-skip-controls.md) is frozen before local beam scoring. Encoder and transition controls now exhaust small three-symbol fixtures and check long rejection runs, rewrite wraparound, key exhaustion and an unrelated advance. A two-symbol ciphertext example also demonstrates that even the correct key can permit multiple plaintexts under key skipping; beam recovery must not be described as guaranteed inversion. The full 216-plant, 2,160-decoder benchmark now passes independent encoder-trace, candidate, score and beam-selection replay. The complete report and receipt are preserved under `experiments/records/decoder-skip-controls/`; a public experiment article, figures and reproduction bundle are still pending. Correct-key rigid addition recovers every plant. Value rewriting frequently passes the score threshold without exact recovery; long runs of key values expose the fixed skip bounds. These are planted-control findings, not conclusions about the manuscript cipher.
