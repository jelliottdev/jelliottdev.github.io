Liberpedia reference-data bundle

Extract this ZIP into an empty folder, keeping its directory structure.
From that folder, with Python 3, run:

  python scripts/reproduce_reading.py --check-all
  python scripts/reproduce_prime_sums.py
  python scripts/rune_ioc.py --check
  python scripts/reproduce_cover_chain.py
  python scripts/reproduce_cover_rsa.py
  python scripts/inspect_visual_records.py

These checks use the included archived texts, records, parameters and evidence.
No network or AI service is needed. CONTENTS.json lists member hashes and roles.

Original JPEGs are provided separately in original-images.zip. Extract that ZIP
into the SAME folder if you want image-based checks. The --pixels option of
inspect_visual_records.py also requires Pillow. extract_payload.py requires
OutGuess, and signature verification requires GnuPG. See the included guides.

This is a data and reproduction bundle, not a complete offline website.
Article source links and wiki navigation may require the live site.
Draft experiment records are not included; published records are included.
The complete repository is available from the GitHub Code download menu.
