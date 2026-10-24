# Which part of a decode does the fold check verify?

**Finding.** The source's fold helper compares **overlapping right-hand tails** of a decoded page. It omits the final fold and never compares the first fold's reference indices. On six new known-key plants, all 30 fold-count trials recover the true text exactly, but changing the first 40 reference indices leaves every measured tail agreement unchanged. Changing every reference index drops every measured tail agreement to zero.

![The five-fold helper compares four overlapping right tails; the first 48 reference indices are never compared.](experiments/records/r21-fold-tail-scope-controls/fold-domains.svg)

The [Round 21 source](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round21/L1-seal-realmode-proxy/hitfn21_folds.py) describes a disjoint-fold check of the held-out complement. Its executable helper first decodes the prefix ending at a fold boundary, then decodes the remaining tail from that prefix's ending key pointer. A final fold has no right-hand tail, so it returns `None`. Earlier prefixes contain all preceding folds, and the compared tails overlap.

| Requested folds | Measured tails | Reference positions compared at least once |
| --- | ---: | --- |
| 2 | 1 | 120–239 |
| 3 | 2 | 80–239 |
| 4 | 3 | 60–239 |
| 5 | 4 | 48–239 |
| 6 | 5 | 40–239 |

Positions above are zero-based. At five folds, for example, four comparisons cover tails starting at 48, 96, 144 and 192. The first 48 reference indices do not enter any agreement calculation. They still affect prefix decoding and the attributed key phase: this is a limit on the **reference comparison**, not a claim that the first ciphertext runes are ignored.

We supplied one fixed 240-rune English plaintext window, three deterministic key seeds and the source's no-suppression or 83% repeat-suppression encoder. The six newly generated ciphertexts use the source `exact` decoder at beam width 400. All six full-page decodes recover 100% of the planted rune indices; every measured tail agrees with its full-page decode at 100%. The three aggregation rules—minimum, mean and fraction above 90%—all return 1.0 for each fold-count trial.

The reference-change controls call the same unmodified source helper on the same ciphertext and key. They change the supplied comparison vector only. Changing its first 40 indices is outside every tested tail, so all tail agreements remain 1.0; changing all indices gives 0.0. These diagnostic controls expose the comparison's scope. They are not wrong-key trials, candidate hallucinations or estimates of a real candidate's correctness.

The runner executes selected source definitions unchanged using Python's syntax tree: the actual `HitDecode` class, baseline held-out helper, fold bounds and fold helpers. It uses the actual bundled beam decoder and English quadgram table. It does not import or replace the unavailable nine-register panel. The separate checker reconstructs each encryption, verifies the traced prefix/tail inputs and key offsets, and independently recounts every agreement and aggregate.

This does **not** replay the original 45 hallucinations, 15-cell catch surface or held-out surrogate, which still require the exact source language panel. The result establishes the executed helper's finite comparison domains; it does not demonstrate that a wrong manuscript reading passes the complete hit gate or that every no-oracle gate must fail.

Run offline with Python 3:

```bash
python experiments/records/r21-fold-tail-scope-controls/run.py
python experiments/records/r21-fold-tail-scope-controls/check.py
python experiments/records/r21-fold-tail-scope-controls/plot.py --check
```

The source, model table, fixed plaintext, plan, traces and MIT license are bundled. No manuscript candidate is searched.
