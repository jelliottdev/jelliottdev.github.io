# Four source texts as running keys

An archived [cipher program](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/advanced_cipher_solver.py) treats **Liber AL**, an authored collection of solved Liber Primus text, Emerson's *Self-Reliance*, and *Deor* as possible running keys. It samples locations in each text, picks the direction and offset with the highest whole-page coincidence, then scores that one output. We replayed this complete source branch on its **18 named pages**.

**Finding:** the best retained output was LP2-08 with Liber AL at offset 2,688. It received source rank score **117.9**. **41 of 49** complete searches over within-page rune-order shuffles scored at least that high. No output is an established reading. The shuffles are a selection reference, not a model of a cipher.

![Four of four full known readings were found at a sampled key offset, none at the tested unsampled offset; the LP2 source score is below the middle shuffled-search score.](experiments/records/wulfic-advanced-running-keys/comparison.svg)

The control is crucial here. We encrypted the unchanged **209-rune First Koan reading** with each of the four texts at offset **300**. The source selector recovered the entire message, correct direction and offset **four times in four trials**. A complete 18-page, four-key synthetic search also ranked its planted reading first. But when the same reading started at offset **137**, between the source's 100-step sampling points, the selector missed it for **all four texts**. These eight plants and the full-grid control were written before the manuscript scores. Thus this replay tests the source's *sampling-and-selection rule*, not every location in the texts.

For each page and text, the program tries offsets `0, 100, 200…` in subtraction, addition and Beaufort directions. It keeps the one with highest normalized `29 × IoC`; only then does it search offsets within 100 places of that winner, in the selected direction. This yields **one retained candidate per page/text pair, 72 in all**. The final score counts English substrings in run-together GP labels and whole words at the page's visible rune separators, then adds `50 × IoC`. It is a rough ranking heuristic, not evidence that an English message has appeared.

The 18 pinned source page streams match the current **LP2-04–17, 26–27, 32 and 37** rune arrays exactly. All four source key streams have distinct byte digests, and the 72 retained decoded outputs are distinct. The authored solved-LP key is the script's own English text, not the independently audited solved rune readings. Existing [Deor/Emerson](#/experiments/wulfic-p21-running-key-layers), [Liber AL](#/experiments/wulfic-liber-al-offset-sweep) and [audited-reading](#/experiments/solved-reading-running-key) records use different programs or key representations; this is one grouped replay of the remaining source branch, not four newly invented cipher ideas.

The [plan](experiments/records/wulfic-advanced-running-keys/plan.json) fixes corpus bytes, page mapping, source offset selection, both planted positions and 49 complete shuffled searches. The [results](experiments/records/wulfic-advanced-running-keys/results.json) retain all 72 source winners and each shuffle's best score; the [control results](experiments/records/wulfic-advanced-running-keys/control-results.json) were produced first. From a full checkout or experiment bundle, provide a separate Git checkout containing the pinned Wulfic revision:

```text
python experiments/records/wulfic-advanced-running-keys/run.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT --check
python experiments/records/wulfic-advanced-running-keys/check.py --source-root PATH_TO_PINNED_WULFIC_CHECKOUT
python experiments/records/wulfic-advanced-running-keys/plot.py --check
```

The original source has no declared license in that checkout, and the three external texts remain in its repository rather than this experiment bundle. The runner checks their Git-blob hashes and executes the original source conversion, decryption and scoring functions. The independent checker reconstructs the key conversion, adaptive offset search, source score, all controls and all 49 complete shuffles without importing that program.
