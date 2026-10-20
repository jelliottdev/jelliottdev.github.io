Liberpedia reference-data bundle

START WITH ONE KNOWN READING
Extract this ZIP into an empty folder and keep its folders together. Open a
terminal in that folder. Use Python 3: on Windows try py --version; on macOS or
Linux try python3 --version. Below, replace python with the command that works.

  python scripts/reproduce_reading.py warning

This decodes LP1-01 with Atbash and checks the literal result against its saved
control. Unusual spellings are preserved intentionally. For setup and a
rune-by-rune explanation, open reference/articles/running-scripts.txt.

CHOOSE A TASK
Check every known reading (nine sections, 17 pages):
  python scripts/reproduce_reading.py --check-all
  Guide: reference/articles/running-scripts.txt

Find a word or phrase in the contextual English readings:
  python scripts/reading_concordance.py circumference --prefix
  Guide: reference/articles/reading-concordance.txt
  This searches known readings, not unsolved ciphertext or hidden messages.

Measure rune frequencies and matching pairs:
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
  Guide: reference/articles/rune-ngrams.txt
  Reports overlapping repeats and source positions under its stated boundaries.

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
  Guide: reference/articles/image-regions.txt
  The ordinary command checks saved records, not newly measured image pixels.

SAVE A RESULT
  python scripts/reproduce_reading.py warning --output warning.txt
  python scripts/reproduce_reading.py warning --trace --output warning-trace.csv
  python scripts/reading_concordance.py circumference --prefix --json --output circumference.json
  python scripts/rune_ngrams.py lp2-31 --length 2 --output lp2-31-bigrams.json
  python scripts/rune_entropy.py lp2-31 --output lp2-31-entropy.json
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
The commands above use the included archived texts, records, parameters and
evidence. No network or AI service is needed. CONTENTS.json lists member hashes
and roles. START-HERE.txt duplicates downloads/REFERENCE-DATA-README.txt for
convenient access after extraction.

Original JPEGs are provided separately in original-images.zip. Extract that ZIP
into the SAME folder if you want image-based checks. The --pixels option of
inspect_visual_records.py also requires Pillow. extract_payload.py requires
OutGuess, and signature verification requires GnuPG. See the included guides.

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
