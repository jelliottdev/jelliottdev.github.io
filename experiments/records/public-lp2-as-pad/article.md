# Could LP2 be the key to another Cicada text?

The usual question is how to decode Liber Primus. This public test reverses the roles: it treats the **12,956 unsolved LP2 runes as a running key** and asks whether that key reveals a shorter Cicada object. It tests specific objects and rules; it does not directly decrypt LP2.

## Finding

**No tested pairing produced a readable English result.** The best of 40 runs scored **−7.032** on the source's English quadgram scale, below its predeclared **−5.5** advancement bar. The five highest-scoring configurations were also compared with 200 shuffled versions of their target each; none exceeded its corresponding highest shuffle score. A planted message encrypted under the same LP2 key *was* recovered, showing that this decoder can succeed on a constructed example of its assumed mechanism.

![Five target groups and their best English scores, all below the advancement bar.](experiments/records/public-lp2-as-pad/scores.svg)

The graphic shows each target's best run. Higher scores are stronger *for this English model*; the plotted values do not measure an unconditional probability that a puzzle idea is true.

## What entered the test

The source's key stream was the 55 nonempty unsolved LP2 transcription segments concatenated in page order. It tested four versions of that stream: forward, reversed, rune-index Atbash (`28 − index`), and negation modulo 29. Each was used with addition and subtraction in `plaintext = (target + sign × key) mod 29`. The decoder can skip up to three key positions at a time when searching for synchronization.

Five targets entered the completed run:

| Target | Input to decoder | Length actually scored |
| --- | --- | ---: |
| 2012–13 puzzle texts | English text converted to rune indices | first 500 |
| Five solved LP1 pages | their recorded plaintext transliterations converted to rune indices | first 500 |
| PGP message text | English text converted to rune indices | first 500 |
| “AN END” byte sequence | hard-coded bytes reduced modulo 29 | 63 |
| LP2 opening | first 200 runes of LP2 tested against the LP2 key | 200 |

The source proposed a sixth target, the pages 49–51 payload, but did **not** have the payload bytes needed to run it. It therefore ran five targets × four key variants × two signs = **40 decodes**. Negating the key and changing the sign gives the same arithmetic as an unnegated key with the original sign, so some decodes are equivalent; 40 is the run count, not 40 independent hypotheses. Every run starts at key offset zero.

The “AN END” input is the **63-byte hard-coded sequence in the source script**, which labels it a SHA-512 hash. This record preserves that exact input without asserting that the bytes independently authenticate an external artifact. The text-to-rune conversion is likewise the source's conversion, not a lossless representation of the original messages.

## What the control and scores mean

The source first encrypted a known English sentence with the LP2 stream, including deliberate key skips. Its beam decoder recovered the planted transliteration exactly, scoring **−4.413**. A rigid decoder using the right key but no skip search scored **−7.334**. That is a useful positive control for this implementation; it cannot prove that an unknown real message, if present, would be found under every different skip pattern or encoding.

The strongest real-target result was the 2012–13 text under the forward LP2 stream with addition: **−7.032**. For that *selected* run, 200 target-order shuffles reached a highest score of **−6.972**, slightly stronger than the observed result. The null comparison was computed for only the top five selected configurations, and the shuffled controls do not repeat the whole selection process across all target and rule choices. We therefore report the observed absence of a hit under the source's gate, rather than a universal statistical exclusion.

This replay uses the [pinned F-01 executable](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/F-01/sweep.py) and [its declared plan](https://github.com/Dukotah/cicada3301/blob/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round16/F-01/PREREG.md). The source's result prose speaks more broadly than its executed grid in places; the figures above come from the machine-readable run and the independent accounting check.

## Reproduce

Download this experiment's ZIP from the record's download control to inspect the pinned code, input texts, result, and checker. From a Liberpedia repository checkout, run:

```bash
python experiments/records/public-lp2-as-pad/check.py
python experiments/records/public-lp2-as-pad/run.py
```

The checker is quick. The complete source replay takes several minutes and runs in a temporary copy, so it leaves the archived result bytes intact. It verifies the complete 40-configuration grid, the positive-control gate, the LP2 rune-stream checksum, the five selected null comparisons, and substantive equality with the pinned source output (excluding elapsed wall time).

The bundled [source results](experiments/records/public-lp2-as-pad/source/liber-primus/analysis/round16/F-01/results.json), [checker](experiments/records/public-lp2-as-pad/check.py), and [figure script](experiments/records/public-lp2-as-pad/plot.py) expose the exact values. The [source README and method notes](experiments/records/public-lp2-as-pad/source/liber-primus/analysis/round16/F-01/PREREG.md) are preserved as evidence of what was proposed, not as broader findings of this replay.

**Remaining scope:** target material other than these five objects, a verified pages 49–51 payload, other key offsets, alternative page boundaries, or using the other objects as key material would require separate tests.
