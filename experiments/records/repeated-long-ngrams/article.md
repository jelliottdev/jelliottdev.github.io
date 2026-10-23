## Finding

**The long repeats are real, but their number is not unusual under a control that preserves each section’s adjacent rune steps.** The 12,956-rune LP2-00–55 transcription contains **six distinct repeated five-rune sequences**, **one repeated six-rune sequence**, and **no repeated seven-rune sequence**. These match the [published inventory](https://github.com/Leo-Y-Zhang/LiberPrimusAnalysis/blob/a32bdc0e06ea58532fbaf4329acae4a0b1020513/results/characterize.txt), including the six-rune `DJUBEI` at zero-based corpus positions **6,555** and **12,950**.

![How often the matched controls produce at least as many long repeated sequences.](experiments/records/repeated-long-ngrams/repeats.svg)

The two overlapping five-rune sequences `DJUBE` and `JUBEI` come from that same `DJUBEI` repeat. They are **not three separate pieces of evidence**. Of 999 controls, 300 reached at least six five-rune repeats, 150 reached at least one six-rune repeat, and 361 reached either threshold. The last comparison counts the decision to notice whichever of the two lengths looks more interesting. The corresponding plus-one proportions are 301/1,000, 151/1,000 and **362/1,000**.

## What was compared

Each control keeps the nine manuscript section lengths, each section’s first rune, and the **exact inventory of its adjacent modular differences**, including rare zero steps. It shuffles the order of those steps within each section, rebuilds the rune stream, joins the sections in manuscript order, and counts distinct repeated sequences of lengths five, six and seven. Windows may overlap and cross joined section boundaries in both the manuscript and controls, matching the source’s corpus-wide counting rule. A planted six-rune copy makes the checker’s repeat count rise from zero to one.

This control asks whether *these counts* distinguish the manuscript from streams with the same step composition. It does not model every possible cipher or decide whether a particular repeat is meaningful. A future claim about `DJUBEI` should specify its predicted location, transformation and successful decoding criterion before inspecting another position. The [complete results](experiments/records/repeated-long-ngrams/results.json) contain every repeated tuple and all 999 control counts.

Run `python experiments/records/repeated-long-ngrams/run.py --check` and `python experiments/records/repeated-long-ngrams/check.py` from the repository root. The second script independently extracts the rune stream, recounts the observed tuples, and reconstructs the first twelve shuffled controls.
