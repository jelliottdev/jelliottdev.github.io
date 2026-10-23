## Finding

**The published A-03 counts reproduce, but they do not establish its claimed limit of 26 missed doubled runes.** The image classifier agrees with the reference transcription at **99.415%**, below the source's **99.5%** gate. Its “planted merges” control adds a number to a formula; it does not insert doubled glyphs into an image and ask the classifier to find them.

![The classifier misses its declared agreement gate; 26 observed excess pairs are not a bound on hidden merges.](experiments/records/a03-haplography-source-gate/gate-audit.svg)

The source reports **108** adjacent-equal image classifications and **82** in the line-by-line reference text, an excess of **26**. It also calculates that **93** additional pairs would reach its stated 1.38% autokey comparison floor. Both subtractions are correct. The leap from “26 observed excess pairs” to “at most 26 transcription merges” needs a measured limit on missed doublets and false image classifications. Neither the source's arithmetic control nor these aggregate counts supplies one. A finite error assignment with 93 true merges, 93 missed image doublets, and 26 false positive image doublets produces the same observed excess. That example establishes the logical gap; it is **not** a claim that those errors occurred.

The source's 7/999 adjacent-equal counts on its count-exact subset are also reproduced from its saved result. A line can have the correct total component count while offsetting one missed component with one extra component. Equality on that subset does not by itself prove there were zero merges.

## What was checked

We pinned the [A-03 source program](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/A-03/a03_hapl_bound.py), its [pre-registered rule](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/A-03/PREREG.md), saved result, and the Round10 classifier receipts by SHA-256. The independent checker rereads the receipt counts, recomputes the 1.38% threshold and the arithmetic control, and verifies the source program loads—but does not subsequently process—the component rows. It likewise cites the older doublet log without parsing it. This is an audit of preserved source output and its inference, **not** an independent image transcription.

The [related duplicate-insertion experiment](#/experiments/haplography-diagonal-bound) answers a different question: whether restoring exact adjacent duplicates changes a particular nonzero-difference statistic. It does not validate A-03's image-based estimate of how many duplicates were missed. This audit does not identify a cipher or show that autokey succeeds.

## Reproduce

With Python 3 and the pinned [source revision](https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1):

```text
python experiments/records/a03-haplography-source-gate/run.py --source-root PATH/TO/liber-primus --check
python experiments/records/a03-haplography-source-gate/check.py --source-root PATH/TO/liber-primus
```

The [plan](experiments/records/a03-haplography-source-gate/plan.json) lists every consumed source hash; the [results](experiments/records/a03-haplography-source-gate/results.json) preserve the counts and the finite counterexample.
