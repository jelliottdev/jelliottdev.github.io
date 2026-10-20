# Liber Primus research wiki

A static reference wiki for the 75 archived Liber Primus page images. Includes transcriptions, documented corrections, known readings, original-image inspection, the Gematria Primus alphabet, and source references.

## Editorial scope

This edition prioritizes source material and factual organization. It does not publish experimental cipher runs or speculative theories. See [editorial conventions](docs/EDITORIAL.md). Coverage is explicitly stated on each page; having a page record does not mean every visual detail has been reviewed.

## Run locally

Run `python -m http.server 8765` from this directory, then open http://localhost:8765. No build or external runtime dependencies are needed for the website.

GitHub Pages serves the main branch at the repository root.

## Data provenance

Original image hashes and pinned public source commits appear in `data/manifest.json`. Page records link directly to public source images. Original image bytes are preserved; thumbnails are cropped derivatives. Reading status is dated to the archived 5 October 2026 snapshot.

To regenerate from the corresponding research archive, install Pillow and run `python scripts/import_archive.py PATH_TO_ARCHIVE .`. The archive is not bundled. The importer verifies all image checksums before copying. Preserve the distinction between archived text and corrected derivatives.

Original manuscript and third-party archive material retain their respective rights; this repository does not assert authorship or grant a blanket license over them.

## Reader, downloads, and AI access

The Reader provides original images beside labeled text versions. Downloads include individual originals and derivatives, verified ZIP bundles, and local SHA-256 checking. Machine readers can use `llms.txt`, `llms-full.txt`, `data/catalog.json`, and the static `reference/` documents without JavaScript. See [access documentation](docs/ACCESS.md) for regeneration and verification.
