# What did the archived keyword-and-route search actually test?

The archived program first applies a proposed repeating keyword to each page, then tries column orders, a magic-square order, spirals, rails, diagonals and other rearrangements. Its files named `page_21` through `page_30` contain **LP2-04 through LP2-13**, respectively. We matched all ten rune streams exactly before replaying the program. The keyword assignments are proposals, not established decryption keys.

## Result

The complete source loop produced **585 reported route rows** across the ten pages. The program also tries all column orders for six short keywords before retaining only each page's best such order. Its highest numerical score differs across pages, but **none of the 585 rows matched even one word** under the program's own word test. The numbers rank English letter pairs in an unbroken stream; they are not evidence of a reading.

![Across ten actual target pages, selected routes raise the source bigram score, while every output has zero recognized words.](experiments/records/wulfic-keyed-transposition-cohort/comparison.svg)

The zero is a property of this *test design*: the program removes spacing and passes the whole output to a function that looks up entire space-separated words. Its pinned repository does not contain the optional `data/wordlist.txt`, so this replay uses its built-in 95-word fallback. The selected strings are far longer than any word in that fallback. A different, explicitly specified word-segmentation test might find short substrings, but that would be a different experiment.

## What the controls establish

We planted known rune messages at each of the ten source lengths. The source keyword-column reversal restored each one, and the source's 25-position magic-square inverse restored each one. Six other route functions preserved full length and the multiset of rune values on every planted stream. **All 80 controls passed.** These checks show the implemented routes run as claimed; they do not validate the proposed page keywords or the English ranking rule.

The source comments promise Myszkowski and disrupted transposition, but `solve_page` never calls either. Its prime-position extraction is not a full-message permutation. We report only the operators actually executed.

## Reproduce and limits

Run `python experiments/records/wulfic-keyed-transposition-cohort/run.py --check --source-file PATH_TO_PINNED_SCRIPT` to repeat the full source loop. Omit `--source-file` to fetch the exact script from its pinned GitHub revision; the runner rejects a different SHA-256. `python experiments/records/wulfic-keyed-transposition-cohort/check.py --source-file PATH_TO_PINNED_SCRIPT` independently checks the page alignment receipts, unchanged-keyword baselines, route selection, and zero-word result. With `--source-repo PATH_TO_PINNED_CLONE`, it also compares all ten archived page files rune by rune with the current LP2 pages. The scripts and saved results are included in the experiment download.

This replay covers the source's exact ten input streams, fixed keyword assignments, routes and scoring rule. It does not test all transpositions or prove that no output can be read under another language or segmentation rule. Four nearby scripts are not silently counted as the same experiment: `p21_30_transposition.py` overlaps the columnar/prime route subset; `p21_30_rearrange.py` requires an absent wordlist for its own score; `p21_30_verified_rearrange.py` additionally requires an absent `verified_keys.json`; and `refine_and_batch.py` adds a stochastic monoalphabetic optimizer and unavailable training inputs. Their unresolved differences remain outside this result.
