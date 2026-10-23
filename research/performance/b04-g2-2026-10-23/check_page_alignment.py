"""Map B04's nonempty source segments to exact Liberpedia rune pages."""
import argparse
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
RUNNER = HERE.parent / "b04-2026-10-23" / "resumable.py"
spec = importlib.util.spec_from_file_location("b04_resumable", RUNNER)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--site-root", type=pathlib.Path, default=HERE.parents[2])
    ap.add_argument("--output", type=pathlib.Path, default=HERE / "page-alignment.json")
    args = ap.parse_args()
    H, S, ks, sk, source_hashes = R.load_source(args.source_root.resolve())
    import lib_numchannel as nc
    from lp import gematria as gp

    site_pages = []
    for i in range(56):
        path = args.site_root / "data/pages" / f"lp2-{i:02d}.json"
        page = json.loads(path.read_text(encoding="utf-8"))
        runes = gp.runes_to_indices(page["raw"])
        assert len(runes) == page["rune_count"]
        site_pages.append({"id": page["id"], "indices": runes,
                           "transcription_sha256": page["transcription_sha256"],
                           "json_sha256": R.sha(path)})

    segments = nc.segments()[:-2]
    assert len(segments) == 55
    mapping = []
    for ordinal, segment in enumerate(segments):
        matches = [page for page in site_pages if page["indices"] == segment]
        assert len(matches) == 1, (ordinal, len(matches))
        page = matches[0]
        mapping.append({"source_segment_ordinal": ordinal,
                        "source_label": f"page{ordinal:02d}",
                        "site_page": page["id"], "rune_count": len(segment),
                        "index_stream_sha256": hashlib.sha256(bytes(segment)).hexdigest(),
                        "site_transcription_sha256": page["transcription_sha256"],
                        "site_page_json_sha256": page["json_sha256"]})
    assert [row["site_page"] for row in mapping] == [
        f"lp2-{i:02d}" for i in list(range(50)) + list(range(51, 56))]
    assert sum(len(s) for s in segments) == 12_956
    assert not site_pages[50]["indices"]
    source_joined = bytes(v for segment in segments for v in segment)
    site_joined = bytes(v for page in site_pages for v in page["indices"])
    assert source_joined == site_joined
    report = {"schema": "b04-source-site-page-alignment-v1",
              "source_revision": R.PIN,
              "source_krisyotam_sha256": source_hashes["data/krisyotam_runes.txt"],
              "source_unsolved_runes": len(source_joined),
              "site_unsolved_runes": len(site_joined),
              "joined_gp_index_sha256": hashlib.sha256(source_joined).hexdigest(),
              "nonempty_source_segments": len(mapping),
              "empty_site_page": "lp2-50",
              "source_to_site": mapping,
              "conclusion": "Every one of the 55 nonempty B04 source segments exactly matches one site rune stream; source page50..54 correspond to site lp2-51..55 after rune-empty lp2-50."}
    R.atomic_json(args.output, report)
    print(json.dumps({"matched": len(mapping), "runes": len(source_joined),
                      "empty_site_page": "lp2-50",
                      "joined_sha256": report["joined_gp_index_sha256"]}))


if __name__ == "__main__":
    main()
