# Do the manuscript JPEGs hash to the deep-web target?

**Result.** No match in either of two clearly separated JPEG sets. The 75 files used by the [published hash lookup](https://github.com/LiberPrimus/Failed-Attempts/tree/d219a8099f8d24e52496e9ee3456ed9980893884/deepweb-hash) are now identified exactly: their SHA-512 **and** BLAKE2b-512 digests match all 150 entries in its saved checksum table. None equals the 128-character target printed on LP2-56. A **new, separate follow-up** on 58 preserved seventh-onion JPEGs also found no match among 116 full-file digests. These results cover two specified byte sets, not the search for any web page that might satisfy the manuscript.

![The 75-image source replay and separate 58-image follow-up both return zero LP2-56 target matches under SHA-512 and BLAKE2b-512.](experiments/records/public-deepweb-jpeg-hashes/source-hash-check.svg)

## Which files were checked?

The source script applies `sha512sum` and `b2sum` to `00.jpg` through `74.jpg`. Its image directory was absent from the pinned repository, so an earlier inventory could only confirm that the archived table contained no target string. We compared **complete 128-digit SHA-512 hashes** from that table with the site's JPEGs. Every row maps uniquely and in order: source `00`–`16` are hosted LP1-00–16, and `17`–`74` are hosted LP2-00–57. Recomputed BLAKE2b-512 hashes also match every saved row. That identifies the exact file bytes used for the source lookup without assuming that identically rendered images have identical bytes.

The 58 preserved JPEGs from the seventh-onion archive are **different bytes** and match none of those source SHA-512 entries. Many hosted copies add only a small JFIF segment, which is enough to change a cryptographic hash completely. Neither preserved repository set is independently authenticated as the puzzle creator's original bytes.

The target is read directly from the five hexadecimal lines in the LP2-56 page record, with only the printed line breaks and trailing slashes removed. Both a SHA-512 lookup and a BLAKE2b-512 lookup over the 75 exact files return no match. As a control, replacing the target with either digest of source image `00` correctly finds that image and no other.

## Separate seventh-onion follow-up

The [preserved seventh-onion image set](https://github.com/neuroretransmit/cicada/tree/ade9a02889ef8acbc8cde8edbfd0a785c369f4c3/2014/011-seventh-onion) supplies `0.jpg` through `57.jpg`. We froze their exact paths, byte lengths and SHA-256 values in a [second candidate plan](experiments/records/public-deepweb-jpeg-hashes/followup-plan.json) before comparing with the target. None of their **58 SHA-512** or **58 BLAKE2b-512** full-file digests matches. A separate planted target using archived `0.jpg` recovers that file under each algorithm. The [complete digest list](experiments/records/public-deepweb-jpeg-hashes/followup-results.json) keeps this follow-up auditable without treating it as a historical run by Failed-Attempts.

## Reproduce

From a complete Liberpedia checkout containing `images/lp1-*.jpg` and `images/lp2-*.jpg`:

```text
python experiments/records/public-deepweb-jpeg-hashes/run.py --check
python experiments/records/public-deepweb-jpeg-hashes/check.py
python experiments/records/public-deepweb-jpeg-hashes/followup.py --check
python experiments/records/public-deepweb-jpeg-hashes/followup-check.py
```

The [source-replay candidate manifest](experiments/records/public-deepweb-jpeg-hashes/plan.json) gives every hosted image path, file size, SHA-256 and the two digest values from the [pinned source checksum table](https://github.com/LiberPrimus/Failed-Attempts/blob/d219a8099f8d24e52496e9ee3456ed9980893884/deepweb-hash/checksums.txt). Each runner verifies file hashes before the target comparison. The two separate checkers parse the printed target from the page's raw lines and recompute both digest families. For download-based reproduction, extract **Original images (ZIP)** alongside this experiment's ZIP so the declared `images/` and `exports/sources/cicada-2014-seventh-onion/` paths exist. A complete repository checkout already includes them.

The source replay covers only its 75 identified JPEGs; the follow-up covers 58 additional, different JPEG bytes. Both use only full-file SHA-512 and BLAKE2b-512. Neither addresses other files, byte transformations, combined files, web pages or a different meaning of “hashes to.”
