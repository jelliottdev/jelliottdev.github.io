# Do random Quagmire alphabets fit LP2's rune frequencies?

A Quagmire-style cipher can relabel plaintext runes, add a key value modulo 29, then relabel the output again. Wulfic's Stage U asks a limited question about that family: **if those relabellings are random**, would the resulting ciphertext usually have rune counts as even as LP2's?

**Finding:** the source's simulation gates pass. Of **24 declared settings**, **20 are excluded** at its strict frequency threshold. The other **four**, all using a uniformly chosen letter from A–Z as the key value, lack enough positive-control power and are **untestable** under the source rule. None is a decryption, and an untestable setting is not support for its cipher.

![Six Quagmire key-value families with twenty excluded and four untestable settings](experiments/records/wulfic-quagmire-random-alphabets/comparison.svg)

The source fixes **six key-value distributions**: English rune values, their prime values, English Latin-letter frequencies, uniformly chosen decimal digits, uniformly chosen hex digits, and uniformly chosen A–Z letters. Each is checked with an independent key alphabet or one tied to the plaintext alphabet. Each of those is checked on the joined **12,956 LP2 runes** and on eight marked sections with fresh alphabets, for **6 × 2 × 2 = 24** settings. The sectioned statistic leaves out the nine-rune header section on LP2-15, as declared in the [source program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_u.py).

## What an exclusion means

For each setting, the source draws **100,000 random alphabet combinations** and asks how often their expected bias would permit LP2's low chi-square value. It requires the probability to be at most **0.0001** both before and after its declared anti-doublet adjustment. It first checks the simulation against known generated ciphers. All six model checks passed; none of the **20 same-family controls per setting** was falsely excluded. A setting can be called excluded only if the rule also rejects at least **18 of 20** flat-key controls. The four A–Z settings fail that power requirement. The [complete 80-row result table](experiments/records/wulfic-quagmire-random-alphabets/source-stage_u_results.tsv) retains every gate and setting.

This result is narrower than “Quagmire was tried.” It uses only overall rune counts and six specified key-value distributions. It says nothing about exact key order, a deterministic keyword alphabet, a different key distribution, another segmentation, or a second cipher layer. Stage T's [independent-random-alphabet bound](#/experiments/wulfic-position-alphabet-flatness-bound) concerns a different model; its warning that a flat *Latin-square* key can escape that bound remains valid. Stage U tests particular Quagmire mixtures with their own controls rather than inheriting Stage T's exclusion.

## Reproduce

The standard-library checker reads Liberpedia's page runes independently, confirms the two manuscript chi-square statistics, and checks all **24** source control/decision rows:

```text
python experiments/records/wulfic-quagmire-random-alphabets/run.py --check
python experiments/records/wulfic-quagmire-random-alphabets/plot.py --check
```

The [plan](experiments/records/wulfic-quagmire-random-alphabets/plan.json) fixes the source revision and simulation rules. To rerun the entire pinned source calculation with NumPy, use:

```text
python experiments/records/wulfic-quagmire-random-alphabets/replay_source.py PATH_TO_WULFIC_CLONE
```

We ran the unchanged program and compared its generated table with the [pinned source result](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_u_results.tsv): all **80 rows match byte-for-byte**. The optional wrapper regenerates the table in a temporary file. The full run takes substantially longer than the bundled checks.
