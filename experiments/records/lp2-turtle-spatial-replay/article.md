# Drawing a path from LP2’s rune numbers

Can the manuscript’s numbers be read as drawing instructions? A [published test](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/B-turtle-spatial-render/PREREG.md) turns each rune into a number, then uses that number to turn and advance an imaginary pen. We independently rebuilt its **72 fixed drawing rules** and checked the resulting paths against its [archived measurements](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/B-turtle-spatial-render/ledger.json). The test asks whether any path forms an unusually orderly figure. It does not turn a path back into decoded words.

![A deliberately planted square, the LP2 prime-value path, and its shuffled control drawn by the same rule](experiments/records/lp2-turtle-spatial-replay/paths.svg)

The left path is a known square placed to check that the renderer can show an obvious shape. The other two use **relative turns and unit steps modulo 4**. One uses the manuscript’s rune order; the other shuffles those same numbers. The manuscript and shuffle panels share a coordinate scale. Their resemblance is a visual comparison for this one rule, not a test of all 72 by itself.

| Question | What this replay found |
| --- | --- |
| Does the published construction reproduce? | **Yes.** The local rune files give the same 12,956-symbol input as the pinned public transcription, and all 72 path settings were rebuilt. |
| Can the drawing method show a deliberate shape? | **Yes.** A planted square closes, and a planted block-comb has perfect measured symmetry. The controls separate from their 200 shuffled versions on multiple recorded measures. |
| Was a decoding rule found? | **No.** A geometric path is not plaintext. The source’s full comparison flagged no path as a glyph or pointer under its declared rule. Our replay reports its precise coverage and statistical limits below. |

## The drawing rule

Every rune has a Gematria Primus prime value. The source tried three number streams: the **prime itself**, its **one-based prime index**, or its **totient** (one less than the prime). For each number it chose a turn on one of six angular grids (4, 6, 8, 12, 29 or 360 directions). The heading either becomes that angle or rotates by that angle. The pen then advances one unit or a distance proportional to the number. These choices make **3 × 6 × 2 × 2 = 72** paths, with no hand-selected route between runes.

The source’s phrase “LP2 pages 0–54” means its first **55 nonempty transcription segments**. Its file omits the blank LP2-50, so its final segment corresponds to **Liberpedia LP2-55**. We verified the source stream against local LP2-00–49 and LP2-51–55 text, rune for rune; the UTF-8 rune-stream SHA-256 is `79b14e630946b64cdca838f328e73904f506df576d15e21fcb46271d4b4c8040`. This matters: stopping at Liberpedia LP2-54 would draw a different 12,880-rune path.

## What the comparison can say

The [source report](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round22/B-turtle-spatial-render/RESULTS.md) compared each path with 200 histogram-preserving shuffles. It measured path closure, sampled self-crossings, occupied raster cells, displacement relative to total travel, symmetry and connected components. We reran **all 14,400 shuffled paths** and reproduced the same **six path/measure pairs** passing the initial, uncorrected screen. None passed the source’s later rule for flagging a candidate figure. That is a **bounded result for these 72 drawing rules and this shape detector**, not a proof that all number-based or geometric readings fail.

The independent path measurements agree with the source to numerical precision except for one sampled crossing in one case; the screen-level conclusion is unchanged. Some reported tail values differ where a real measurement and shuffled values are equal to machine precision. The source’s two-sided counting formula can even return a value above 1 for ties, so those numbers are best read as screening ranks rather than precise probabilities.

Two of the six measurements, **closure** and **caging**, are the same net-displacement divided by path-length formula. They should not be read as separate confirmation. The source also used a normal-tail approximation to refine rare events beyond what 2,000 shuffled samples can measure directly; that tail estimate depends on the approximation, especially for discrete counts such as connected components. The source therefore reports a useful controlled screen, while a strong claim about a specific picture would still need an independently frozen recognizer and a larger suitable null.

This record keeps geometry separate from language. A meaningful text read along a path could leave no distinctive drawn figure. Conversely, a visually suggestive walk would need an explicit rule for selecting and reading symbols before it could count as a decryption.

## Reproduce

From the repository root:

```text
python experiments/records/lp2-turtle-spatial-replay/run.py --check
```

This checks the pinned rune stream, all 72 constructed paths, the planted controls and the saved result. `--full-null --check` additionally repeats the 200 shuffles for every path. The script needs Python 3, NumPy and SciPy; the visual is regenerated with `python experiments/records/lp2-turtle-spatial-replay/plot.py`. The [saved results](experiments/records/lp2-turtle-spatial-replay/results.json) contain every path’s measurements and comparison differences; [source measurements](experiments/records/lp2-turtle-spatial-replay/source-ledger.json) are preserved verbatim from the pinned revision for offline checking.
