## Finding

**LP2's shortage of repeated adjacent runes looks like a rule applied to a continuous rune stream.** The source compared the manuscript with simulated streams that all have the *same* low adjacent-repeat rate. The real text matches the model whose only special treatment is at lag one. It differs from the tested models that also avoid recently used runes or rebalance a short window. A model that resets the rule at each printed line is rejected by where the remaining repeats fall.

That is a comparison among specified generators, **not proof that a computer rather than a person applied the rule**. The source's own weakest “hand” model starts with machine-generated symbols and applies only the same adjacent-repeat check. It cannot be separated from the machine-filter model here (combined power **0.110**). What the test supports is a lag-one-only, line-continuous filter *signature*; it does not identify the author's implementation or the pad's source.

![The manuscript's window balance sits with a matched lag-one filter, while tested recency-avoidance models produce substantially stronger balancing.](experiments/records/lp2-filter-fingerprint-models/filter-models.svg)

## What separates the models

The **12,956-rune** unsolved stream contains **86 identical adjacent pairs**, or **0.664%** of adjacent positions; unrelated uniform runes would match about **3.45%** of the time. The controls were calibrated to that same **0.664%**, so merely finding fewer repeats cannot decide between them.

| Check | Manuscript | Matched controls | Reading |
|---|---:|---:|---|
| Equal runes at lags 2–8 | **3.488%** | A lag-one-only filter leaves these near the **3.448%** chance rate. | No clear extra recency avoidance. |
| Rune balance in 58-rune windows, χ²/df | **0.936** | Lag-one-only mean **0.943**; weakest tested recency model **0.881**. | The apparent short-window balance is already produced by the lag-one rule. |
| Doublets spanning a printed line | **4 of 86** | Continuous filter mean **4.8%** of doublets; line-reset filter mean **22.9%**. | The observed **4.7%** agrees with a continuous filter, not the tested line-reset rule. |

The source pre-registered a 200-replicate model ladder and required at least **80% measured power** before a feature could vote. Its calibration gate separates uniform streams from the lag-one filter with power **1.000**. Five tested hand-style models with additional recency or rebalancing effects are classified against the matched filter; the no-extra-effect rung remains **underpowered to separate**. The line-scope control also has power **1.000** for the specified reset rule. Those power figures depend on the tested generators and sample length.

The source labels its overall result “MACHINE.” We use the narrower conclusion above because a person's exact application of a lag-one-only rule to an otherwise machine-like stream is observationally equivalent under this battery. The line-reset comparison rejects *that reset model*, not every plausible way a person could maintain the rule across lines.

## Scope and input check

Our separate parser reproduces the **86 doublets**, **four line-crossing doublets**, lag-2–8 rate, same-rune gap variation, 29/58/116/290-rune window measures, and page-level doublet dispersion to the source's displayed precision. It finds **594 nonempty physical lines**. The source reports **648 lines** because its global line ordinal advances through slash-delimited empty slots; there are **649 slots** including the trailing one. Its numerical source run uses that ordinal geometry. The two line counts describe different things and should not be compared as if they were rival transcriptions.

The model ladder is a bounded falsification of several proposed ways the filter might behave. It is not a decryption, a proof of an OTP, or a survey of every human-randomness strategy. In particular, its 95% bound on additional lag-2–8 suppression assumes the fitted lag-one control's variation and the source's pooled-lag statistic.

## Reproduce

With Python 3, the independent measurement needs only the bundled transcription:

```text
python experiments/records/lp2-filter-fingerprint-models/run.py
python experiments/records/lp2-filter-fingerprint-models/check.py
python experiments/records/lp2-filter-fingerprint-models/plot.py
```

The [result data](experiments/records/lp2-filter-fingerprint-models/results.json) exposes the directly measured counts. The bundled source includes the original pre-registration, 200-replicate control script and pinned result receipt. The separate `replay-source.json` is a fresh run of that exact source script from the pinned repository revision; the checker requires both the source gate and the independently reconstructed manuscript statistics to agree. All reported model means, powers, bounds, and verdicts reproduce. Auxiliary AUC values vary where scores tie; they do not enter the declared gate.
