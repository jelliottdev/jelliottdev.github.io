# Do the six proposed *Night Thoughts* lines point to 729?

A [reported book-pointer idea](#/wiki/reported-attempts?section=night-thoughts-729-book-pointer) starts with the **729 runes** on LP2-00–02, then gathers what it calls line 729 from Nights IV–IX of Edward Young’s *Night Thoughts*. The discussion supplies six short quotations and a [Google Books volume](https://books.google.com/books?id=GsVHv1gACYAC), but does not verify the scan’s edition or give a cipher rule for using the collected lines.

Here we checked the **six quoted locations**, using one pinned comparison text: the [1853 edition edited by George Gilfillan](https://www.gutenberg.org/ebooks/33156), transcribed as Project Gutenberg ebook 33156. It is a later text, **not a claimed replay of the linked Google scan** or Blake’s 1797 illustrated volume. We retained its full UTF-8 text and license in the downloadable experiment, normalizing only CRLF line endings to LF, so its printed line-number markers can be checked offline.

![Night IV through IX compared with the reported line 729; five entries show 729, while Night IX shows 731 in the pinned 1853 edition.](experiments/records/night-thoughts-729-line-audit/line-729.svg)

## What the lookup shows

The archived page transcriptions contain **262 + 266 + 201 = 729** alphabet runes across [LP2-00](#/page/lp2-00), [LP2-01](#/page/lp2-01) and [LP2-02](#/page/lp2-02), counting headings and excluding every non-rune. That establishes the proposed *pointer value*, not a link to any book.

The six quoted passages are all identifiable in the pinned edition. Its right-margin verse numbers, checked against adjacent numbered lines, place **five** of them at line 729. The Night IX phrase, “And deep reception, in th’ intender’d heart,” is at **line 731**: the edition numbers “With gain, and joy, she bribes thee to be wise” as 728, followed by two intervening lines before the quoted phrase. The source’s wording also differs slightly from this edition in places, such as “series end” versus “series ends.”

| Night | Short identifying words | Line in the pinned 1853 text |
| --- | --- | ---: |
| IV | “Hold her sacred still” | 729 |
| V | “thunder scarce obtains your ear” | 729 |
| VI | “in man the series ends” | 729 |
| VII | “blind Passion! drive us on” | 729 |
| VIII | “the Muse, to win thine ear” | 729 |
| IX | “deep reception … intender’d heart” | **731** |

This **5-of-6 result is edition-specific**. The Google Books scan linked in the discussion might use different text or numbering; we could not verify its title page and all six page locations from a pinned copy. The source also lists printed pages 82, 110, 150, 182, 230 and 276 for the six selections. Their sum is 1030, but this audit does not certify those page labels in that scan. No probability of a literary connection follows from five positional matches in a book whose six passages were selected after inspection.

## What a cipher test would still require

Combining six lines in chapter order is a text selection, not a decryption. A test needs one identified edition; the exact extracted six lines, including the Night IX discrepancy; a normalization and rune conversion; a rule for applying the text to a stated manuscript span; and a success criterion assessed on an untouched continuation. Any search across alternative Nights, editions, page counts, RSA parameters or word arrangements must include those choices in its control search.

The [plan](experiments/records/night-thoughts-729-line-audit/plan.json) fixes the six source quotations, comparison edition and location procedure. The [result](experiments/records/night-thoughts-729-line-audit/results.json) preserves each exact line, file coordinate and neighboring numbered markers. From a checkout or extracted bundle, run:

```text
python experiments/records/night-thoughts-729-line-audit/run.py --check
python experiments/records/night-thoughts-729-line-audit/check.py
```

Both use only Python’s standard library. The independent checker uses separately read line and marker coordinates and confirms the three page-rune counts; it does not import the producer.
