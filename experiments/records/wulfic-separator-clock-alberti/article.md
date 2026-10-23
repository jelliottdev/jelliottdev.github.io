# An alphabet that turns at runes and separators

An archived solver tried a changing alphabet with two clocks: one shift after each rune and another after a word or other visible separator. **None of its eleven LP2 targets passes its own frequency gate**, whether we preserve its literal rune parser or correct a glyph omission. This is a bounded result for the source's specified shifts and target pages; it is not a test of every Alberti disk or changing alphabet.

![Each LP2 page's highest collision score under the two-clock grid remains below the source's 1.4 hit gate.](experiments/records/wulfic-separator-clock-alberti/comparison.svg)

The chart shows the largest **normalized index of coincidence** (a measure of repeated rune values) after trying every source clock setting on each page. The source calls a result a hit only above **1.4**. Its best LP2 value is **1.164** with the original parser and **1.159** when the missing rune is restored. There are **zero gated outputs** on either representation. The source also listed old page 15, which is actually solved **LP1-15**; its literal parser produced two gate-passing settings there. That solved page is displayed in the [result table](experiments/records/wulfic-separator-clock-alberti/results.json) but excluded from the LP2 comparison.

## What was tested

At position `i`, the alphabet has turned by `letter_shift × i + separator_shift × separators_before_i` modulo 29. The source tries every shift from **0 to 28**, both directions and three decode modes. That is **5,046 named settings** per page, but they collapse to **1,682 distinct outputs**: opposite directions and arithmetic signs often describe the same transformation. We retained the source's page list, zero starting phase, separator rule, IoC gate, and bigram/trigram ranking above that gate. The selected old source page ordinals map to the LP2 pages labeled in the chart.

The original program lists `ᛂ` where the archived manuscript uses `ᛄ`. As a result, its literal parser drops **5–13 runes** from each named LP2 page. We show that exact parser and a separately declared canonical-GP correction. The correction is a *new input variant*, not a reconstruction of a historical run. A second source issue is path placement: the archived script changes into `tools/` and then looks for a `pages/` directory there. Our replay reads the exact pinned Git page files instead. These old files match the site's archived rune sequence before applying the source parser.

## How strong is the result?

Before testing LP2, we used four archived known readings to make **eight planted messages**, one under each parser per reading. A chosen two-clock schedule recovered all eight exactly, and all eight cleared the source's 1.4 gate. We also compared 24 cases directly with the pinned source decoder. The independent checker reconstructed every observed page and all **49 complete-search shuffled controls**. None of those shuffled controls cleared the gate either. That control has too few positive hits to assign a useful tail probability to the LP2 zero; it does show that merely searching many clocks does not force a hit under this threshold.

The outcome is limited to the eleven source-selected LP2 pages, these two parsers, the page-local two-clock rule, and the source's gate. Adding a constant starting phase only renames the output symbols, so it cannot change IoC or make this gate pass. Other separator meanings, alphabets, plaintext languages, and extra cipher layers remain open. A readable passage or an independently predicted held-out page would be needed to support a new clock rule.

## Reproduce

The [frozen plan](experiments/records/wulfic-separator-clock-alberti/plan.json), [source-page snapshot](experiments/records/wulfic-separator-clock-alberti/inputs.json), [gate receipt](experiments/records/wulfic-separator-clock-alberti/gate_results.json), and [results](experiments/records/wulfic-separator-clock-alberti/results.json) carry the exact bytes and case counts. In the extracted experiment folder, `python check.py` independently repeats the page and control censuses; `python plot.py` regenerates the chart. To repeat source parity, use `python gate.py --source-root ABSOLUTE_PATH_TO_PINNED_WULFIC_CLONE`. To repeat all computations after the gate, run `python run.py --check`. To regenerate the input snapshot, run `python snapshot_inputs.py --source-root ABSOLUTE_PATH_TO_PINNED_WULFIC_CLONE --liberpedia-root ABSOLUTE_PATH_TO_LIBERPEDIA_CHECKOUT`.
