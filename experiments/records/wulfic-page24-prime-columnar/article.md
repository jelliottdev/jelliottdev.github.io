# Prime positions and column order on LP2-07

**Result.** The archived page-24 search's best trigram score was **225**. Running its complete 377-setting search on 256 shuffled versions of the same page produced a score at least that high **222 times**. The selected output does not provide evidence of a reading under this scorer.

![Best trigram scores from the manuscript and 256 full-search shuffled controls](experiments/records/wulfic-page24-prime-columnar/comparison.svg)

The [source scripts](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p24_prime0_post.py) call this *page 24*. Its pinned rune text matches **LP2-07** here, rune for rune. There are 208 runes. The original scripts point to a page directory that does not exist at that relative path in the pinned repository, so we replayed their stated operations using the pinned page object. We do not treat a missing archived output as a historical negative result.

## What was tried

The [first source script](https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p24_char_tests.py) produces seven views of the page: runes at one-based prime positions, runes at **zero-based** prime positions, the zero-based nonprime complement, and whole-page column readings at widths 5, 7, 11, and 13. A zero-based prime index of 2 picks the **third** rune; a one-based prime position of 2 picks the **second**. Both select 46 runes here. The one-based direct extraction is already included in [Runes at prime and Fibonacci positions](#/experiments/prime-fibonacci-position-extraction); this record adds the source-specific zero-based and columnar steps.

The second source script takes only the 46 zero-based-prime runes. It lays them in rows of width **2 through 14**, reads down columns, then subtracts each shift **0 through 28** modulo 29. That is **13 × 29 = 377 settings** in one search. Its fixed scorer joins the rune names into Latin letters and sums a short list of weighted three-letter fragments. The highest score came from width **10**, shift **16**. The [full result file](experiments/records/wulfic-page24-prime-columnar/results.json) preserves every score and output hash.

The source also prints index of coincidence (IoC), but it cannot rank these 377 settings: column reading only rearranges the same 46 runes, and a uniform shift relabels them. Every setting therefore has exactly the same GP29 IoC, **0.981**. The four whole-page column readings likewise all have the page's IoC, **1.043**. Their output streams are recorded as observations; the source specifies no separate pass rule for them.

## How to read the comparison

Each control shuffled all 208 runes within LP2-07, then repeated the **whole 377-setting selection**. The observed maximum's add-one comparison is **223/257 ≈ 0.868**. A synthetic page with a repeated THE pattern planted at the zero-based prime positions passed the exact selector, column reading, shift, and source trigram scorer; its best full-search score exceeded 49 synthetic random-page controls. This checks the implementation and a favorable pattern, not whether the short source scorer recognizes real prose reliably.

This is a bounded test of a **46-rune selection on one page**. It does not exclude another index origin, a further cipher layer, different page boundaries, or a different language model. A few weighted fragments in a selected short string would not establish a decryption.

The [frozen plan](experiments/records/wulfic-page24-prime-columnar/plan.json) fixes the operations and controls. Run `python experiments/records/wulfic-page24-prime-columnar/check.py` for an independent reconstruction of every setting and shuffle, or `python experiments/records/wulfic-page24-prime-columnar/run.py --check` to repeat the saved result.
