Liberpedia reference-data bundle

Extract this ZIP into an empty folder, keeping its directory structure.
From that folder, with Python 3, run:

  python scripts/reproduce_reading.py --check-all
  python scripts/reproduce_prime_sums.py
  python scripts/rune_ioc.py --check
  python scripts/rune_ngrams.py lp2-31 --length 2
  python scripts/reproduce_cover_chain.py
  python scripts/reproduce_cover_rsa.py
  python scripts/reproduce_emerson.py
  python scripts/inspect_visual_records.py
  python scripts/check_number_examples.py
  python scripts/reading_concordance.py circumference --prefix

These checks use the included archived texts, records, parameters and evidence.
No network or AI service is needed. CONTENTS.json lists member hashes and roles.

To save a known reading or its rune-by-rune trace as UTF-8:
  python scripts/reproduce_reading.py warning --output warning.txt
  python scripts/reproduce_reading.py warning --trace --output warning-trace.csv
These create files in your current folder and refuse to overwrite existing files.

Original JPEGs are provided separately in original-images.zip. Extract that ZIP
into the SAME folder if you want image-based checks. The --pixels option of
inspect_visual_records.py also requires Pillow. extract_payload.py requires
OutGuess, and signature verification requires GnuPG. See the included guides.

Optional frequency chart:
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
