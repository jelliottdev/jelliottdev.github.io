# Could the LP2-56 number be four MD5 hashes?

The ending of [LP2-56](#/reader/lp2-56) prints 128 hexadecimal characters: **64 bytes**. One bounded way to read them is as four consecutive 16-byte values, the length of an MD5 digest. We compared each complete block with MD5 of the exact bytes in the preserved Liberpedia artifact corpus.

**Result: none of the four blocks matched.** The corpus contains 412 named variants representing 324 distinct byte strings. We computed MD5 once per distinct input and made **1,296 exact block comparisons**. Each block had zero hits.

![Four consecutive 16-byte blocks of the LP2-56 printed value, each with zero exact MD5 matches in the fixed candidate corpus.](experiments/records/lp2-56-four-md5-target-blocks/blocks.svg)

This closes only the stated construction for these inputs. It does **not** show that LP2-56 is not a sequence of MD5 values: the intended input could be a web page or other bytes absent from the corpus. Nor does it test modified encodings, another reading of the printed value, truncated digests, a different offset, or a different algorithm. If all four blocks had candidate matches, a proposed four-part explanation would still need to justify the input selection and printed order; no such ambiguity arose here.

## Exact input and comparison rule

The target is the five hexadecimal runs between separators in the archived LP2-56 reading, with the terminal slash marks removed. Decoding those 128 characters gives 64 bytes. Blocks start at byte **0, 16, 32, and 48**; each occupies exactly 16 bytes. The comparison uses binary digest bytes, not their printed hexadecimal characters.

The [frozen artifact corpus](#/experiments/lp2-56-internal-artifact-hashes) consists of original page JPEGs, four precise text-encoding variants of stored page raw text and section readings, plus one resolved 256-byte grid payload. Their paths and SHA-256 hashes are pinned in its [source plan](experiments/records/lp2-56-internal-artifact-hashes/plan.json). That earlier experiment tested three 64-byte digest algorithms against the **whole** printed LP2-56 target. This record asks the distinct four-block MD5 question. The [aligned grid-payload test](#/experiments/lp2-56-aligned-digest-blocks) instead compares artifact hashes with blocks of a different, **256-byte grid payload**.

The runner verifies the printed target against the archived page text and all candidate source-file hashes. It checks MD5 of `abc` against its standard test value, then plants known MD5 digests at the first and last blocks of a synthetic 64-byte container. The independent checker rebuilds the candidate bytes, hashes them and checks all four block positions and the controls. The controls pass, including rejection of byte-reversed digest matches.

Run from the repository root:

```text
python experiments/records/lp2-56-four-md5-target-blocks/run.py --check
python experiments/records/lp2-56-four-md5-target-blocks/check.py
```

The [plan](experiments/records/lp2-56-four-md5-target-blocks/plan.json), [results](experiments/records/lp2-56-four-md5-target-blocks/results.json) and [checker](experiments/records/lp2-56-four-md5-target-blocks/check.py) pin the bytes, bounds and outputs. This is a new test of a specific construction, **not** a replay of a claimed historical attempt.
