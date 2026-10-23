# How many independent key alphabets would LP2 need?

If each key value selects its own **unrelated, randomly chosen rune alphabet**, repeatedly using only a few key values should leave a measurable bias in the ciphertext. Wulfic's Stage T asks how many effectively distinct key values that model needs before LP2's nearly even rune counts cease to be surprising. “Effective” accounts for uneven key frequencies: 29 equally used values give 29 effective classes; a key dominated by a few values has fewer.

**Finding:** under the source's declared 1-in-10,000 lower-tail rule, the model is excluded through **168 effective key classes** if one set of alphabets serves the joined LP2 text. If each of eight marked sections gets a fresh set, the source's bound is **174**. Larger class counts are **not excluded**, which is not evidence that they decrypt anything. This is a bound on one kind of random substitution scheme, not an identified cipher or a reading.

![Two conditional effective-class bounds, 168 and 174](experiments/records/wulfic-position-alphabet-flatness-bound/comparison.svg)

The joined test uses all **12,956 runes** on LP2-00–55. The sectioned test uses **12,947**: source sections 7–9 and 11–15, omitting a nine-rune section at the start of LP2-15 as its rule specifies. These are [marked sections of the pinned transcription](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/data/canonical/liber_primus_master.txt), not necessarily whole pages. The independent checker reconstructed them from Liberpedia's page text and reproduced the source's pooled chi-square **26.36** and eight-section sum **194.14**.

## What was tested

The model gives each key value a separate random permutation of the 29-rune alphabet. A fixed value always uses its assigned permutation. The test measures the overall rune counts, without selecting a key phase or fitting plaintext words. The [source program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_t.py) calibrated the model using the rune distribution of solved LP1 text. Before inspecting the manuscript statistic, its declared gates passed on **200 generated ciphers** each at 29, 256 and 1,024 classes. At 1,024 classes, **0 of 200** controls were falsely excluded at the strict threshold.

The source also evaluated **20 specified key-class schemes**. Fifteen fell below the conditional bound, including prime values reduced modulo 29 and the source's byte streams reduced modulo 29. Five raw-byte classings, with roughly 236–255 effective classes, were not excluded. That says only that this frequency test lacks the power to reject them. It does not validate those byte files as puzzle keys. See the [complete source table](experiments/records/wulfic-position-alphabet-flatness-bound/source-stage_t_results.tsv) for each classing and its effective count.

The source reports a stricter **153/133** pair after scaling the observations by a factor learned from an additive control. This was a **post-run sensitivity check**, not the declared rule that produced 168/174. An additive or Vigenère-style *Latin-square* alphabet can look flat even with few key classes; Stage T does not reject that family. It also does not cover correlated or deliberately balanced substitution alphabets, transposition, or additional layers.

## Reproduce

From the Liberpedia repository root, these standard-library checks verify the source table hash, the control decisions, independent LP2 rune counts and statistics, the analytic pooled boundary, and the figure:

```text
python experiments/records/wulfic-position-alphabet-flatness-bound/run.py --check
python experiments/records/wulfic-position-alphabet-flatness-bound/plot.py --check
```

The [plan](experiments/records/wulfic-position-alphabet-flatness-bound/plan.json) pins the source revision and rules. For a complete Monte Carlo replay, including the **2,000,000-draw** sectioned reference, run the optional wrapper with a matching external checkout and NumPy:

```text
python experiments/records/wulfic-position-alphabet-flatness-bound/replay_source.py PATH_TO_WULFIC_CLONE
```

It runs the unchanged source program into a temporary file. Its **45 output rows match the pinned published results byte-for-byte**. The independent bundled check verifies the manuscript statistics and pooled analytic boundary; the sectioned Monte Carlo bound is verified by that full source replay.
