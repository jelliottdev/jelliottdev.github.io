## Question and result

A candidate can look convincing simply because we tried many keys and kept the best output. Comparing that winner with one randomly chosen wrong key would ignore the selection step. Here, each control repeats the **whole declared search** and keeps its best score, just as the real search would.

The best control scores rise as the nested dictionary grows from one to 256 keys, but none crosses the fixed −5.5 acceptance threshold in this grid. Searches of encrypted known text also fail that threshold when the true key is absent. Appending the true key makes every such control recover exactly and pass. This shows that the scorer can recognize the known answer **when this search includes it**; it does not establish a false-positive rate for larger or different searches.

## Three conditions, kept separate

| Condition | Ciphertext | Keys searched | What it checks |
| --- | --- | --- | --- |
| Null | Reproducible uniform pseudorandom rune indices | A declared wrong-key dictionary | The best score selected from the whole dictionary under this null generator. |
| Positive, key absent | A known rune prefix encrypted by addition modulo 29 | The same dictionary, excluding its true seed | What a search reports when its intended answer is outside its bounds. |
| Positive, key included | The same positive ciphertext | That dictionary plus its true key | Whether inclusion recovers the known answer and whether it wins the scoring comparison. |

The included condition has **one more candidate** than the stated wrong-key budget. At budget 256 it compares 257 candidates. Its known key is not secretly inserted into the other conditions, and its exact-recovery check is separate from score acceptance.

## Inputs and bounds

All nine known-reading traces contribute their first 240 output rune indices, or their full length when shorter. Their lengths range from 85 to 240 runes. These are existing trace outputs, not edited English converted back into runes. No section is removed because of a poor score or unusual content.

For each section, 32 replicates generate a null ciphertext and a positive ciphertext of that section's length. Each null uses a fresh, recorded Python pseudorandom-generator seed and uniform draws from indices 0–28. Each positive uses the known prefix and a recorded derived key. The paired controls share length and search settings; they do not share ciphertext.

The candidate keys use SHA-256 over a fixed ASCII seed label and a four-byte big-endian counter, with digest bytes reduced modulo 29. Because 256 is not divisible by 29, this reduction is biased. It is an explicit fixture, not a uniform-pad claim. Candidate seeds are 0–255; positive seeds are 100000–100031 and therefore absent from that dictionary.

For every candidate, subtract its key from the ciphertext modulo 29, transliterate with the canonical rune labels, and average the English quadgram log scores. The unseen-quadgram count is 0.01 and the threshold is −5.5, inherited unchanged from the [scorer controls](#/experiments/english-scorer-controls). There are no offsets, alternate signs, skip rules or word-boundary adjustments.

## Nested search budgets

Every search retains all 256 individual candidate scores and examines dictionary prefixes of 1, 4, 16, 64 and 256 keys. A larger budget contains every candidate in the smaller one. Its maximum therefore cannot decrease. Ties use the smallest seed ID, including when comparing an appended true key.

The figures preserve all nine source sections. At each budget, a dot is the median of the 32 best scores and the vertical line is their full observed range. Neither is a confidence interval. All panels share a score scale. The positive included condition has a constant score within a section because exact decryption returns the same known rune prefix despite different encryption keys.

| Wrong-key budget | Null accepted | Positive accepted, true key absent | Positive exact and accepted, true key included |
| --- | ---: | ---: | ---: |
| 1 | 0/288 | 0/288 | 288/288 (2 candidates) |
| 4 | 0/288 | 0/288 | 288/288 (5 candidates) |
| 16 | 0/288 | 0/288 | 288/288 (17 candidates) |
| 64 | 0/288 | 0/288 | 288/288 (65 candidates) |
| 256 | 0/288 | 0/288 | 288/288 (257 candidates) |

These are counts over the fixed grid, not independent-trial accuracy estimates. The full CSV keeps each section separate across all 135 section/budget/condition combinations. The JSON retains all 147,456 wrong-key scores, 288 true-key controls, ciphertexts, seeds, candidate hashes and search winners.

## What a zero count means

We observed no threshold exceedances among these null searches. That does not prove the threshold is safe for a million-key search, a beam decoder, several language models, or repeated human choices about which output to keep. Such procedures offer different opportunities to find a high-scoring candidate and need their own controls.

The sections share source material, the dictionary is reused, and budgets are nested. Repetition does not turn this into 288 independent texts drawn from all possible plaintext. The null generator is also a chosen model, not an established description of the manuscript. We do not estimate a probability that a manuscript candidate is correct, pool the scores into an anomaly verdict, or infer a cipher family.

The [decoder alignment controls](#/experiments/decoder-skip-controls) demonstrate a complementary limitation: even a correct key can fail under an unsuitable decoder, and an incorrect rune sequence can pass a language score. Here the positive controls validate only ordinary modular addition and this declared dictionary search.

## Reproduce and inspect

Extract the experiment ZIP with its folder structure intact. Python 3 and its standard library are sufficient; there are no network requests, API calls or paid services.

```text
python experiments/records/search-maximum-controls/run.py --check
python scripts/check_search_maximum_controls.py experiments/records/search-maximum-controls/results.json --receipt my-search-audit.json
python experiments/records/search-maximum-controls/plot.py
```

The independent checker imports no producer functions. It rebuilds the source prefixes, null ciphertexts and derived keys, checks every candidate hash, recalculates scores using counted quadgrams, and reconstructs every winner and tie decision. It also checks monotonic maxima and the additional candidate count when the true key is appended. All 288 paired searches passed; human review remains pending.

The practical lesson is to compare a selected result with controls that undergo the same selection. See [search space and bounds](#/wiki/search-space) and [null models](#/wiki/null-models). A different dictionary, decoder, scoring rule or adaptive workflow should be a documented variant, with the complete search repeated in its controls.
