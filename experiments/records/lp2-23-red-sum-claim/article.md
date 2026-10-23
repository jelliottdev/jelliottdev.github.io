## What was summed

The stored red opening on [LP2-23](#/reader/lp2-23) contains **16 runes totaling 786**, including the enlarged initial. The phrase **TEST THE KNOWLEDGE** totals **691** when `TH` is one rune and the K sound uses GP `C`. Those are different totals. The supplied compilation's item 13.3 does not include the original post or a different explicitly marked rune span, so its historical calculation cannot be reconstructed from this claim alone.

![The archived red heading sums to 786. The proposed phrase sums to 691 with one TH rune or 768 with separate T and H runes.](experiments/records/lp2-23-red-sum-claim/red-sums.svg)

| Input | Rune groups | Word sums | Total |
| --- | --- | --- | ---: |
| Stored red opening | 2 / 6 / 3 / 5 | 100 + 268 + 123 + 295 | **786** |
| TEST THE KNOWLEDGE, single TH | 4 / 2 / 9 | 238 + 72 + 381 | **691** |
| Same phrase, separate T and H | 4 / 3 / 9 | 238 + 149 + 381 | **768** |

The original page was inspected to locate the red opening and its transition to black text. Glyph identities in this test remain those of the archived transcription; this is not an independent adjudication of every glyph.

## The 95-point difference

The stored second rune is `A`, worth 97. Substituting `F`, worth 2, would lower 786 to 691 exactly. That is a **sensitivity check, not a correction**: no source supplied here justifies changing that rune. An image-level disagreement or a different claimed span would need its own evidence.

Even an equal sum would not translate the heading. A sum discards word order: TEST THE KNOWLEDGE and KNOWLEDGE THE TEST necessarily have the same value. The phrase also has a different rune-count and word-length pattern from this heading. A proposed reading needs a fixed decoding rule and continuation, not only a numerical match.

## Reproduce

```text
python experiments/records/lp2-23-red-sum-claim/run.py --check
python experiments/records/lp2-23-red-sum-claim/check.py
python experiments/records/lp2-23-red-sum-claim/plot.py --check
```

The arithmetic uses only the bundled standard-library scripts, alphabet and text. The [plan](experiments/records/lp2-23-red-sum-claim/plan.json) names the exact prefix, spelling choices and original-image hash. The separate checker generates the first 29 primes and verifies every header value without importing the producer. For visual inspection use the [original JPEG](images/lp2-23.jpg); original page images are supplied separately from experiment ZIPs.
