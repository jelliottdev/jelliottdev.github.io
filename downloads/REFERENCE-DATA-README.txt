Liberpedia reference-data bundle

START WITH ONE KNOWN READING
Extract this ZIP into an empty folder and keep its folders together. Open a
terminal in that folder. Use Python 3: on Windows try py --version; on macOS or
Linux try python3 --version. Below, replace python with the command that works.

  python scripts/verify_bundle.py REFERENCE-DATA-CONTENTS.json
  python scripts/reproduce_reading.py warning

The first command checks the extracted files against the included manifest.
Continue when it reports zero problems; otherwise investigate the named files.
See VERIFY THE EXTRACTED FILES below for the limits of that check.
The second command decodes LP1-01 with Atbash and checks the literal result against its saved
control. Unusual spellings are preserved intentionally. For setup and a
rune-by-rune explanation, open reference/articles/running-scripts.txt.

RUN ONE EXPERIMENT
Published experiment records and articles are included here. Their scripts,
source inputs and saved outputs are in separate, complete experiment ZIPs:
  https://jelliottdev.github.io/downloads/experiments/<record-id>.zip
Find the record ID and bundle URL in data/experiment-index.json. Extract the
chosen ZIP into an empty folder and follow its START-HERE-<record-id>.txt.
This keeps the reference download small as the experiment archive grows.

CHOOSE A TASK
Check every known reading (nine sections, 17 pages):
  python scripts/reproduce_reading.py --check-all
  Guide: reference/articles/running-scripts.txt

Find a word or phrase in the contextual English readings:
  python scripts/reading_concordance.py circumference --prefix
  Guide: reference/articles/reading-concordance.txt
  This searches known readings, not unsolved ciphertext or hidden messages.

Locate the exact page of a literal decoded word:
  python scripts/reading_concordance.py circumference --literal --prefix
  Guide: reference/articles/reading-concordance.txt (Locate a word on an exact page)
  Joins archived line wraps and reports page and literal-line locations.
  Preserve label spelling: DIUINITY and UOICE, rather than DIVINITY and VOICE.
  JSON output retains the original excerpt and per-page source hashes.

Measure rune frequencies and matching pairs:
  python scripts/compare_transcriptions.py text/lp2-00.txt text/lp2-00.txt
  python scripts/rune_ioc.py lp2-31
  python scripts/rune_ioc.py --check
  Guide: reference/articles/index-of-coincidence.txt
  The first measures one archived page; the second verifies the saved baseline.
  A descriptive statistic is not a cipher identification or a significance test.

Measure single-rune frequency entropy:
  python scripts/rune_entropy.py lp2-31
  Guide: reference/articles/rune-entropy.txt
  Reports bits per rune from the observed counts. This does not measure sequence
  order, identify a cipher, or test whether a page is random.

Locate repeated rune sequences:
  python scripts/rune_ngrams.py lp2-31 --length 2

Find fixed-substitution-compatible positions (rune labels, not English words):
  python scripts/rune_crib.py lp2-42 --crib "F U F U TH" --output crib-matches.json
  This checks equality patterns, ignores separators, and includes headings.
  It does not recover a key or assign significance to a match.
  Guide: reference/articles/rune-ngrams.txt
  Reports overlapping repeats and source positions under its stated boundaries.

Count equal runes at fixed distances:
  python scripts/rune_lag_matches.py lp2-31 --max-lag 20
  Guide: reference/articles/rune-lag-matches.txt
  Reports a numerator and denominator for every lag, without circular wraparound.
  A peak does not establish a period or key length. The saved example is in
  exports/lp2-31-lag-matches.json and exports/lp2-31-lag-matches.csv.
  The SVG chart is at exports/figures/lp2-31-lag-matches.svg.

Generate a bounded set of shift candidates:
  python scripts/enumerate_shifts.py lp2-31 --output my-shifts.json
  Guide: reference/articles/reproducibility.txt (Generate the 58 cases yourself)
  Saves all 29 shifts for original and reversed rune order, with the input hash.
  This is candidate generation: no score, match test, or conclusion is supplied.
  An output file is required. Existing files are never replaced.

Reproduce numerical examples:
  python scripts/reproduce_prime_sums.py
  python scripts/check_number_examples.py
  Guides: reference/articles/prime-sums.txt and prime-indices.txt

Reproduce the earlier puzzle chains:
  python scripts/reproduce_cover_chain.py
  python scripts/reproduce_cover_rsa.py
  python scripts/reproduce_emerson.py
  Guides: reference/articles/cover-chain.txt, cover-rsa.txt,
  and emerson-self-reliance.txt
  These replay historical results from local evidence; they do not contact the
  historical addresses or discover new solutions.

Inspect recorded visual measurements:
  python scripts/inspect_visual_records.py
  python scripts/measure_region.py lp2-56 --rect 800 2350 900 500
  Guide: reference/articles/image-regions.txt
  The ordinary command checks saved records, not newly measured image pixels.

Compare fixed cuneiform windows (requires original-images.zip and Pillow):
  python scripts/measure_cuneiform_windows.py --check
  Guide: reference/articles/cuneiform.txt
  This remeasures decoded pixels and checks the recorded file hashes and results.

Audit equal adjacent runes (no significance test):
  python scripts/rune_doublets.py --check
  python scripts/test_rune_doublets.py
  Guide: reference/articles/doublets.txt

Reconstruct unsolved word-length counts (no English corpus test):
  python scripts/rune_word_lengths.py --check
  python scripts/test_rune_word_lengths.py
  Guide: reference/articles/word-lengths.txt

SAVE A RESULT
  python scripts/reproduce_reading.py warning --output warning.txt
  python scripts/reproduce_reading.py warning --trace --output warning-trace.csv
  python scripts/reading_concordance.py circumference --prefix --json --output circumference.json
  python scripts/rune_ngrams.py lp2-31 --length 2 --output lp2-31-bigrams.json
  python scripts/rune_entropy.py lp2-31 --output lp2-31-entropy.json
  python scripts/rune_lag_matches.py lp2-31 --max-lag 20 --output my-lag-counts.json
These create UTF-8 files in your current folder and refuse to overwrite existing
files. For the concordance, --json selects JSON; the filename alone does not.
Preserve the input hashes and counting rules alongside any interpretation.

VERIFY THE EXTRACTED FILES
  python scripts/verify_bundle.py REFERENCE-DATA-CONTENTS.json
After extracting original-images.zip into the same folder, also run:
  python scripts/verify_bundle.py ORIGINAL-IMAGES-CONTENTS.json
The checker reads files without changing them and reports missing or changed
members. Extra files are not checked. Matching a manifest does not authenticate
its source. The separately named manifests survive combining the bundles;
CONTENTS.json is a compatibility copy belonging to the last bundle extracted.

WHAT IS INCLUDED
For subject discovery, data/topics.json contains topic titles, categories,
summaries, search terms, links, and evidence notes. reference/topics.txt is its
readable counterpart. These are navigation records, not completed experiments;
use data/experiments.json for the reviewed experiment registry.

The commands above use the included archived texts, records, parameters and
evidence. No network or AI service is needed. CONTENTS.json lists member hashes
and roles. START-HERE.txt duplicates downloads/REFERENCE-DATA-README.txt for
convenient access after extraction.

Original JPEGs are provided separately in original-images.zip. Extract that ZIP
into the SAME folder if you want image-based checks. The --pixels option of
inspect_visual_records.py, measure_region.py and measure_cuneiform_windows.py also require Pillow. extract_payload.py requires
OutGuess, and signature verification requires GnuPG. See the included guides.

DRAW THE ATBASH MAPPING
  python scripts/plot_atbash_pairs.py --output my-atbash-pairs.svg
This uses the standard library and included alphabet, with no extra packages.
Open the SVG in a browser. The chart pairs indices i and 28-i; it illustrates
ordinary Atbash, not the additional shift used by the first koan.
A ready-made copy is at exports/figures/atbash-pairs.svg.
Guide: reference/articles/atbash.txt

OPTIONAL FREQUENCY CHART
  python -m pip install matplotlib
  python scripts/plot_rune_frequencies.py --output my-rune-frequencies.svg
Only the installation step may need network access. The plot reads local saved
counts and refuses to overwrite an existing output. Matplotlib is not needed
for rune_ioc.py --check. A ready-made chart is included at
exports/figures/rune-frequencies.svg. Keep package versions with shared figures.

This is a data and reproduction bundle, not a complete offline website.
Article source links and wiki navigation may require the live site.
Draft experiment records are not included; published records are included.
The complete repository is available from the GitHub Code download menu.
