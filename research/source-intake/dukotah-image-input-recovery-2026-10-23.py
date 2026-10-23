"""Byte audit only; never substitutes an image or runs a source experiment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "source-cache" / "dukotah-cicada3301" / "liber-primus"
CAPTURE = ROOT / "exports" / "sources" / "cicada-2014-seventh-onion"
MANIFEST = SOURCE / "handoff" / "capsule" / "MANIFEST.json"
OUT = Path(__file__).with_suffix(".json")


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {int(x["id"].split("p")[-1]): x for x in manifest["items"] if x.get("id", "").startswith("images.onion7.p")}
    assert set(entries) == set(range(56)), "capsule has 56 pinned LP2 image hashes"
    rows = []
    for i in range(56):
        entry = entries[i]
        site = ROOT / "images" / f"lp2-{i:02}.jpg"
        capture = CAPTURE / f"{i}.jpg"
        assert site.is_file() and capture.is_file()
        site_hash = digest(site)
        site_sha1 = digest(site, "sha1")
        capture_hash = digest(capture)
        rows.append({
            "source_page": f"p{i}.jpg",
            "source_expected_sha256": entry["sha256"],
            "source_expected_bytes": entry["bytes"],
            "source_published_sha1": entry.get("published_sha1"),
            "hosted_local_path": str(site.resolve()),
            "hosted_sha256": site_hash,
            "hosted_sha1": site_sha1,
            "hosted_bytes": site.stat().st_size,
            "hosted_exact_match": site_hash == entry["sha256"] and site.stat().st_size == entry["bytes"],
            "hosted_published_sha1_match": site_sha1 == entry.get("published_sha1"),
            "other_saved_capture_path": str(capture.resolve()),
            "other_saved_capture_sha256": capture_hash,
            "other_saved_capture_exact_match": capture_hash == entry["sha256"],
        })
    assert all(x["hosted_exact_match"] for x in rows)
    assert all(x["hosted_published_sha1_match"] for x in rows)
    assert not any(x["other_saved_capture_exact_match"] for x in rows)

    onion = []
    for i in range(3):
        path = ROOT / "images" / f"lp1-{i:02}.jpg"
        onion.append({"candidate": f"onion{i+1}.jpg", "local_path": str(path.resolve()),
                      "bytes": path.stat().st_size, "local_sha256": digest(path),
                      "local_md5": digest(path, "md5"),
                      "exact_source_hash_available": False,
                      "note": "The pinned R29/L1 report provides no complete digest for this onion-chain file; name/size/appearance alone do not establish byte identity."})
    onion[2]["source_reported_md5_prefix"] = "497f911a"
    onion[2]["source_reported_bytes"] = 175159
    onion[2]["prefix_and_size_match"] = onion[2]["local_md5"].startswith("497f911a") and onion[2]["bytes"] == 175159

    prerequisites = {
        "template_npz": {"source_path": "analysis/retranscribe/templates.npz", "present_in_pinned_checkout": (SOURCE / "analysis/retranscribe/templates.npz").is_file(),
                         "regeneration_route": "Source templates.py takes glyphs2.npz; could be regenerated from exact images after segment2.py. No original NPZ digest in the source manifest, so regeneration is not proof of byte identity or the original numeric output."},
        "geometry_npz": {"source_path": "analysis/geometry/glyphs2.npz", "present_in_pinned_checkout": (SOURCE / "analysis/geometry/glyphs2.npz").is_file(),
                         "regeneration_route": "Source segment2.py reads p0..p55.jpg, all now byte matched. Rerun can be attempted in an isolated checkout and checked against published line/glyph counts; no original NPZ digest is pinned."},
        "font_bank": {"source_path": "analysis/round18/L1-toolchain/fonts/", "present_in_pinned_checkout": (SOURCE / "analysis/round18/L1-toolchain/fonts").is_dir(),
                      "regeneration_route": "Source get_fonts.sh has URLs, but upstream font versions may have changed; download and pin each binary before treating a rerun as the same 11-font bank."},
        "onion_chain_jpegs": {"source_path": "analysis/armada_osint/artifacts/dl_onion{1,2,3}.jpg", "present_in_pinned_checkout": all((SOURCE / f"analysis/armada_osint/artifacts/dl_onion{i}.jpg").is_file() for i in range(1, 4))},
    }
    lanes = [
        {"source_id": "A-04", "matched_source_jpegs": [49, 50, 51], "jpeg_input_unblocked": True,
         "remaining": "Exact page bytes recovered, but source crop/calibration and the Round19 adjudication still require their full method and positive control; this audit does not verify any of the six contested glyphs."},
        {"source_id": "A-06", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "The LP2 renders are exact. Its reader.py additionally loads missing analysis/retranscribe/templates.npz; the LP1/solved calibration-image lineage and all source controls require separate checking."},
        {"source_id": "G-01", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "Direct JPEG fingerprinting can use exact bytes. Two-stage pipeline controls need newly generated synthetic PDFs and Ghostscript/ImageMagick tool versions; the source PDF/font used to make LP2 remains unavailable."},
        {"source_id": "B-11", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "Glyph extraction loads missing analysis/retranscribe/templates.npz. The specified candidate font bank is absent; the site's single bundled Noto font does not recreate the source bank or its controls."},
        {"source_id": "B-12", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "Image and line-geometry arms now have exact page bytes. The ornament/reader arm also depends on missing templates.npz and source-generated geometry/results; preserve each arm's separate control gate."},
        {"source_id": "R12-frontB", "matched_source_jpegs": list(range(45, 55)), "jpeg_input_unblocked": True,
         "remaining": "The ten target JPEGs are exact, but forceseg.py needs missing templates.npz. The source's forced-segmentation control failed at 12.923%; recovering images alone does not turn that result into a valid negative."},
        {"source_id": "R29-L1-ONION-STEGO", "matched_source_jpegs": [], "jpeg_input_unblocked": False,
         "remaining": "Likely hosted LP1-00..02 candidates have matching descriptions/sizes and onion3 has the reported eight-digit MD5 prefix, but pinned R29/L1 publishes no complete target digest and original dl_onion1..3 files are absent. No byte-exact source match is certified for the 4,013-key stego sweep; exact outguess/steghide versions also matter."},
        {"source_id": "R30-A1-FONT", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "font_signature.py's main page images are exact; its native Python/Pillow/NumPy/SciPy method and output must still pass an independent control and source-result check. Its wider known-font identity comparison still lacks the source font bank."},
        {"source_id": "R30-A2-SUBPIXEL", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "classpure.py additionally loads missing analysis/geometry/glyphs2.npz; exact image bytes do not replace per-glyph geometry or its classifier-link controls."},
        {"source_id": "R30-A3-PDF-FORENSICS", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "Embedded ICC/JPEG marker checks can use exact pages. The original authoring PDF and font remain absent, so controls may bound a renderer family but cannot identify the exact production file."},
        {"source_id": "R30-B1-BLOB-CRYPTO", "matched_source_jpegs": [], "jpeg_input_unblocked": False,
         "remaining": "Its source battery reads extracted T2.bin, folly.bin and canon_256.bin, not the 56 LP2 page JPEGs. This image recovery does not authenticate those blob inputs."},
        {"source_id": "R30-B2-RSA-GPG", "matched_source_jpegs": [], "jpeg_input_unblocked": False,
         "remaining": "Its source additionally reads the stage04 2.jpg file and appended payload; the 56 LP2 page-image matches do not authenticate that separate image or its extraction."},
        {"source_id": "R30-C1-ART-ATTRIBUTION", "matched_source_jpegs": "p0..p55", "jpeg_input_unblocked": True,
         "remaining": "The image corpus is exact, but visual source-image attribution requires independently pinned reference artwork and cannot be settled by matching the page bytes alone."},
        {"source_id": "R30-E1-RENDER-REOPEN", "matched_source_jpegs": [49, 50, 51], "jpeg_input_unblocked": True,
         "remaining": "Table pages are exact. Reopening the contested I/l glyph calls still needs an independently checked reading; source notes the shapes are identical in its candidate font, so geometry alone cannot close those cells."},
    ]
    return {
        "schema": "liberpedia-source-input-recovery-v1",
        "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "source_manifest_path": str(MANIFEST.resolve()),
        "source_manifest_sha256": digest(MANIFEST),
        "scope": "Byte-level input audit only; no source method, score, control or conclusion is replayed.",
        "summary": {"hosted_manuscript_images": len(list((ROOT / "images").glob("lp1-*.jpg"))) + len(list((ROOT / "images").glob("lp2-*.jpg"))),
                    "manifest_lp2_images": len(rows), "hosted_exact_matches": sum(x["hosted_exact_match"] for x in rows),
                    "hosted_published_sha1_matches": sum(x["hosted_published_sha1_match"] for x in rows),
                    "saved_capture_exact_matches": sum(x["other_saved_capture_exact_match"] for x in rows),
                    "hosted_lp1_onion_candidates": 3, "lp1_onion_candidates_source_hash_verified": 0},
        "lp2_source_images": rows,
        "lp1_onion_candidates": onion,
        "remaining_non_image_prerequisites": prerequisites,
        "lane_input_status": lanes,
        "caution": "The saved seventh-onion capture files are a distinct JPEG byte version, even where decoded pixels match. Use the hosted LP2 bytes only for the Dukotah manifest-defined relikd input; do not substitute one byte version in JPEG/steganography tests without a new scope declaration."
    }


if __name__ == "__main__":
    receipt = build()
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(receipt["summary"])
