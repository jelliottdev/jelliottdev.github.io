# Does the sieve's pass gate require every register?

A proposed first-pass filter for Liber Primus keys was meant to retain at least 90% of planted correct keys in **all nine tested text groups (languages and altered English forms)**, while reducing the candidate pool at least 100-fold. Its [source decision function](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round20/P1/build_surface.py) does not check that all nine registers were measured before returning `PASS`.

This new function-level control supplies every nonempty subset of the nine named registers, with reported survival fixed at 95% and reduction fixed at 100-fold. The function returns `PASS` for **all 511 subsets**, including **510 that omit at least one required register**. It also reports `all9_survival_pass=true` for each. These are deliberately constructed measurement summaries, not new ciphertext decodes.

![All incomplete high-survival register subsets pass the source function; the saved source result remains infeasible.](experiments/records/round20-sieve-register-gate/coverage.svg)

The cause is a coverage condition: the function computes its all-register check over the registers **present** in the input. A cell containing only `LP1_REAL` can therefore receive the same `PASS` label as a cell containing all nine. The code explicitly permits subset measurements, which makes a separate completeness condition necessary if `PASS` is to mean that the full requirement was met. The four gate-register and two kill-register checks also skip absent registers.

Comparison controls establish the boundaries of this result. A complete nine-register summary at 95% survival and 100-fold reduction passes. Lowering Welsh survival to 89% prevents the full pass, although the other four gate registers still earn the source's partial label. Lowering reduction to 99-fold produces `SHORTFALL`. The defect concerns missing measurements, rather than those two numerical thresholds.

Reapplying the unchanged source function to its **four saved pilot files exactly reproduces every archived cell**. All four remain `SHORTFALL`; their best simultaneous Welsh/half-vowel English survival at sufficient reduction is **2/3**, and the archived overall decision remains `INFEASIBLE`. One pilot measured six of the nine named registers, plus the separate random control, but its measured failures already prevent a pass. This control does **not** show that the source's published infeasibility decision is wrong.

The saved pilot measurements are source outputs. The Marsaglia plants, offset scans, model training and downstream manuscript searches were not rerun. Exact Welsh training bytes and the corresponding panel model remain unavailable locally. No missing corpus was substituted. The result is a bounded software-contract finding: a future high-survival subset must not be mistaken for evidence about unmeasured registers.

The [offline runner](experiments/records/round20-sieve-register-gate/run.py) bundles the exact source decision file, four pilot files, archived surface and license. The [independent checker](experiments/records/round20-sieve-register-gate/check.py) verifies source hashes, exhaustive subset coverage, comparison controls and saved-pilot parity:

```bash
python experiments/records/round20-sieve-register-gate/run.py --check
python experiments/records/round20-sieve-register-gate/check.py
```
