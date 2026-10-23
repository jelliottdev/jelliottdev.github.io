"""Check the fresh B winner's head key under source Stage-D key lengths."""
import hashlib
import json
import pathlib

import audit_stage_continuity as A

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path(
    "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301")
MERGED = pathlib.Path(
    "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/b04-lp2-B-20261023/merged.json")


def audit():
    H, S, ks, sk, hashes = A.R.load_source(SOURCE)
    data = json.loads(MERGED.read_text(encoding="utf-8"))
    row = data["rows"][0]
    assert row["dir"] == "fwd" and row["offset"] in (1, 4, 16, 29, 64,
                                                       128, 256, 512, 1024, 3301)
    head, page, book = H.head_segment(), H.full_page0(), H.full_unsolved()
    assert head[1] == page[1][:120] == book[1][:120]
    seed = bytes.fromhex(row["seed_hex"])
    offset = row["offset"]
    b_requested = 3301 + 120 * (H.MAX_SKIP + 2) + 128
    page_requested = len(page[1]) + offset + 512
    book_requested = len(book[1]) + offset + 512
    keys = {"B_worker": A.worker_key(ks, row["gen"], row["red"],
                                      seed, b_requested),
            "D_page0": ks.make_ks(row["gen"], row["red"], seed,
                                  page_requested),
            "D_book": ks.make_ks(row["gen"], row["red"], seed,
                                 book_requested)}
    # Compare every byte of the shorter key, not only the first 120 symbols.
    prefix_equal = {
        "B_vs_D_page0": keys["B_worker"][:min(map(len, (keys["B_worker"], keys["D_page0"]))) ] ==
                        keys["D_page0"][:min(map(len, (keys["B_worker"], keys["D_page0"])))],
        "B_vs_D_book": keys["B_worker"][:min(map(len, (keys["B_worker"], keys["D_book"]))) ] ==
                       keys["D_book"][:min(map(len, (keys["B_worker"], keys["D_book"])))],
    }
    c = head[1] if row["atbash"] == 0 else head[2]
    decoded = {name: sk.beam_decode(c, key, sign=row["sign"], o=offset,
                                    beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
               for name, key in keys.items()}
    assert decoded["B_worker"]["score"] == row["score"]
    return {"schema": "b04-b-winner-to-d-head-continuity-v1",
            "source_revision": A.R.PIN, "source_hashes": hashes,
            "stage_b_merged_sha256": A.R.sha(MERGED),
            "configuration": {k: row[k] for k in
                              ("seed_hex", "gen", "red", "sign", "atbash",
                               "dir", "offset", "score")},
            "requested_key_lengths": {"B_worker": b_requested,
                                      "D_page0": page_requested,
                                      "D_book": book_requested},
            "actual_key_lengths": {name: len(key) for name, key in keys.items()},
            "first120_key_sha256": {name: hashlib.sha256(
                bytes(key[offset:offset+120])).hexdigest()
                for name, key in keys.items()},
            "shorter_key_prefix_identical": prefix_equal,
            "same_120_ciphertext": A.digest_symbols(head[1]) == A.digest_symbols(
                page[1][:120]) == A.digest_symbols(book[1][:120]),
            "head_decode_scores": {name: result["score"]
                                   for name, result in decoded.items()},
            "head_decode_text_sha256": {name: hashlib.sha256(
                result["translit"].encode()).hexdigest()
                for name, result in decoded.items()},
            "scope_limit": "Only the B winner's 120-rune head was decoded under D key lengths; no full Stage D decoding was run."}


if __name__ == "__main__":
    result = audit()
    out = HERE / "b-winner-continuity.json"
    out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                              indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"prefix_equal": result["shorter_key_prefix_identical"],
                      "head_scores": result["head_decode_scores"],
                      "output": str(out)}, sort_keys=True))
