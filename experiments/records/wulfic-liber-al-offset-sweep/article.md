# Does the Liber AL text work as a key for LP2-08?

An archived program turns *Liber AL vel Legis* into rune values, slides that key across a page, and scores the results for six common English letter triples. Its archived `page_25` file matches **LP2-08**, not LP2-25. We ran the program's complete offset-selection rule on the corrected 255-rune page and the exact text bytes pinned in its repository. This is a new test on corrected inputs; the original output file is unavailable.

## What happened

The best output scored **670** on the program's common-trigram scale. That is ordinary under a simple order control: **154 of 199** shuffled versions of the same rune sequence scored at least as high when the *entire* search was rerun. The shuffle comparison asks whether this score stands out from rearranged page symbols. It is not a model of encryption or a probability that the book is irrelevant.

![The source's offset selection misses an off-grid planted message, while the page score sits below the shuffle median.](experiments/records/wulfic-liber-al-offset-sweep/comparison.svg)

The program samples offsets 0, 100, 200, and so on through 5,000, then searches within 200 positions of its six strongest first-stage rows. On this page it examined **2,104 distinct refined offsets** in two cipher directions, producing **4,310 scored rows** including the coarse rows. It does not examine every possible starting position.

That limit mattered in a direct test. Four known messages planted at sampled offsets 300 and 1,700, in both directions, were recovered. The same clear message planted at offset **137** was missed in both directions: its neighborhood never qualified for the finer search. So this result does **not** rule out an offset the source procedure skipped.

## What this covers

The source's exact rune alphabet, greedy text-to-rune conversion, two decryption directions, weighted `THE`/`AND`/`ING`/`ION`/`ENT`/`TIO` score, IoC tie-break, first six coarse rows, and ±200 refinement were retained. We only redirected paths moved by the source repository's own archiving. The page file and book text were verified against pinned Git objects before use. The source's old optimizer outputs are explicitly disclaimed in its archive, so none was treated as a confirmed key or reading.

A high score here means those short letter triples appeared in an unbroken transliteration. It is not a readable passage by itself. Other page identities, editions, key encodings, offsets outside the selected neighborhoods, and the follow-on substitution hill climber remain untested by this record.

## Reproduce

From a clone of the [pinned Wulfic revision](https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c), run `python experiments/records/wulfic-liber-al-offset-sweep/run.py --source-repo PATH_TO_CLONE --check`. The runner verifies the source script, page and book hashes, then recomputes the complete result. `check.py` independently rebuilds all selected rows and all 199 shuffle controls; it also compares 40 short random cases with the source's own decryptor and scorer. The exact search bounds and input hashes are in the bundled plan and results. `plan-frozen.json` preserves the byte-for-byte plan saved before scoring; `plan.json` adds only the archive's dependency-list format.
