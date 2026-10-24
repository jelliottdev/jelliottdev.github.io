# Independent autokey source/control review

No manuscript target was loaded or scored. Scope is the pinned `run_full_new.py --mode autokey` driver plus `autokey_skip.py`, not its smoke command. Producer paths are parameters in the retained independent scripts; there are no private absolute paths in them.

## Executable scope

The driver supplies 29 singleton primers and 16 literal words, all 45 encoded arrays distinct; both P/C models and both signs on 55 source segments give 9,900 labelled calls. Width 450, max skip 3, complete segment, page-local reset, offset zero, no Atbash, no short screen. Strict source score gate is >−5.5. The driver itself does not call the original `gate()`; this study separately reproduces that source gate before target. Source labels and source segment numbering must not be confused with method counts or physical page IDs.

The source gate uses only 90 runes at width 500 for its decision. On its own longer paragraph, P recovers completely but C matches only 67.45% despite both 90-rune gates passing. The gate's match denominator is the smaller output length; complete-length recovery must be reported separately. In this actual nonempty-primer grid, however, the decoder returns full length, so do not invent observed truncation failures from that latent denominator flaw.

## P causal frontier and completeness proof

Let the primer length be m≥1, i the zero-based position of the last decoded rune, and a its accepted key pointer. The key available after i runes is `primer + decoded path`. For the next rune, accepted pointer a' must satisfy a'<m+(i+1), hence a'−(i+1)≤m−1. The initial state has pointer0 at position0. Therefore at every completed position, `0≤a−i≤m−1`: at most m−1 total skips are permitted in the entire P output.

Conversely, every retained state always has a valid no-skip continuation: choose a'=a+1, which is within the already available key by the invariant. No rejected-key conditions apply to that branch. Thus `nxt` cannot be empty for nonempty input and primer. The source's break/short-return path is unreachable solely from this frontier in the actual 45-primer grid. Every independent control and parity fixture returned its complete length.

For m=1 the invariant forces a=i everywhere. All 29 singleton P branches are exactly rigid plaintext autokey, with no skipped key position and a single beam path: 29×2 signs×55 segments=3,190 rigid labels inside the 9,900-label enumeration. Retain them, but do not market them as newly skip-aware coverage. Different inputs/scores still need specific overlap comparison with older rigid records.

## Encoder and decoder do not define identical plants

P encoder has the entire true plaintext available in advance, and later substitutes zero beyond its end. P decoder can only consult the path already decoded. C encoder substitutes zero for ciphertext positions not yet emitted; C decoder instead has the complete observed ciphertext available up front, followed by zero padding. The source suppression is stochastic 0.83 with a >40 retry escape, whereas the decoder admits at most three rejected positions per transition. Neither a large skip count nor a future query alone is a universal proof of plaintext impossibility: an alternate admissible path can exist. The independent oracle enumerates all pointer paths for each fixed true reading.

## Independent completed checks

- `parity-receipt.json`: 228 frozen synthetic cases and 15,761 ordered native terminal hypotheses. Compiled/native paths, pointers, Latin lengths, cumulative scores, stable ordering and returned dictionaries agree exactly. All outputs are complete. The 66 singleton-P fixtures also match rigid decoding exactly. Cases cover every primer, both signs/models, repeated-input ties and lengths through 277.
- `controls-audit-receipt.json`: all 360 source-generated control ciphertexts, RNG paths, skip counts and key-use lengths independently reconstructed; truth-feasibility DP independently checked; every native full control beam and 56,063 native terminal hypotheses inspected. Independent raw-model normalized score error is zero. All eight wrong-primer passing outputs were also checked natively. There are no safety-break events or short outputs.

| Model | Trials | Admissible truth | Exact recovery | Score passes | Wrong-primer passes |
|---|---:|---:|---:|---:|---:|
| P | 180 | 54 | 54 | 54 | 0 |
| C | 180 | 59 | 59 | 99 | 8 |

Every admissible true reading is recovered; none is pruned or outscored. The other 247 readings are not valid plaintexts under the decoder's source rules. In these specific trials, all 126 P inadmissibilities coincide with encoder future-plaintext/end-zero queries; all 121 C inadmissibilities coincide with encoder zero-future-ciphertext queries. This observed equivalence is not a universal theorem about other seeds. Encoder paths exceeding three skips occur in 32 P and 94 C cases and are retained separately.

The C score passes include 40 incorrect own-key readings. These controls reuse two known readings, rather than representing 360 independent messages. They validate implementation fidelity and identify model mismatch; they do not validate a general autokey-family rejection. Any target run needs an explicit pretarget amendment limiting its purpose to complete historical algorithm measurement and retaining these failures, then root authorization.
