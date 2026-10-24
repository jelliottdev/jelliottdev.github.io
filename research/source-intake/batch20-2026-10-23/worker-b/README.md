# Worker B: source-bound audit of eight entries

These are provenance/source-correction/instrument-planning entries, not eight new cipher tests. Read `receipt.json` for per-entry completed scope and remaining prerequisites.

Executed `audit.py`, the source JPEG parser self-test (6/6), and `finite_checks.py`. Exact pinned source objects and hashes are in `source-manifest.json`; cryptographic message evidence is in `signature-results.json` and `audit-results.json`. The GPG check uses an isolated public-only keyring, not the user keyring. Dates are signature-packet claims, not independent historical timestamps.

The key and source-message hashes in the older source table use CRLF; pinned Git blobs use LF. Every one of the 57 compared source files agrees under that explicit normalization. Their signature validity was tested on pinned LF bytes, not inferred from delimiter counts.

The two substantive discrepancies are a signed PGP MESSAGE missed by delimiter-only checks, and 1,252 retained candidate rows in the current pinned snapshot versus the source saved total of 1,312. The same retained-row source function was executed; its 113 consumed inputs were checked against pinned Git object IDs (allowing only CRLF/LF conversion).

`gnupg/` and the two generated Pillow JPEGs are local execution scratch. They are not proposed webpage assets. No font bank was downloaded and no source instructions were adopted.

Source copies are a local cache, not duplicated in this repository. `audit.py` restores missing objects from the shared `work/source-cache/dukotah-cicada3301` Git checkout at the revision pinned in the script and verifies their hashes before use. This requires Python, Pillow, GnuPG, and that checkout. The batch checker can verify uncached evidence directly from the same Git objects.
