"""Audit B04 A-screen versus D-escalation keystream continuity, without D runs."""
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "b04_resumable", HERE.parent / "b04-2026-10-23" / "resumable.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def digest_symbols(values):
    return hashlib.sha256(bytes(values)).hexdigest()


def worker_key(ks, gen, red, seed, nsym):
    raw = ks.make_bytes(gen, seed, int(nsym * 1.35) + 256)
    return ks.make_ks(gen, red, seed, nsym, raw=raw)


def audit(source_root, stage_a_merged):
    H, S, ks, sk, hashes = R.load_source(source_root)
    a = json.loads(stage_a_merged.read_text(encoding="utf-8"))
    assert a["stage"] == "A" and a["complete"]
    top = a["rows"][0]
    assert top["offset"] == 0 and top["dir"] == "rev"
    head = H.head_segment()
    page = H.full_page0()
    book = H.full_unsolved()
    assert head[1] == page[1][:len(head[1])] == book[1][:len(head[1])]
    seed = bytes.fromhex(top["seed_hex"])
    head_len = len(head[1])
    a_nsym = head_len * (H.MAX_SKIP + 2) + 128
    d_page_nsym = len(page[1]) + 512
    d_book_nsym = len(book[1]) + 512
    a_key = worker_key(ks, top["gen"], top["red"], seed, a_nsym)[::-1]
    page_key = ks.make_ks(top["gen"], top["red"], seed, d_page_nsym)[::-1]
    book_key = ks.make_ks(top["gen"], top["red"], seed, d_book_nsym)[::-1]
    ciphertext = head[1] if top["atbash"] == 0 else head[2]
    head_decodes = {}
    for label, key in (("A_worker_key", a_key), ("D_page0_key", page_key),
                       ("D_book_key", book_key)):
        decoded = sk.beam_decode(ciphertext, key, sign=top["sign"],
                                 o=0, beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
        head_decodes[label] = {"score": decoded["score"],
                               "translit_sha256": hashlib.sha256(
                                   decoded["translit"].encode()).hexdigest(),
                               "first64": decoded["translit"][:64],
                               "pointer_end": decoded["ptr_end"]}
    assert head_decodes["A_worker_key"]["score"] == top["score"]
    assert head_decodes["A_worker_key"]["first64"] == top["head"]

    forward_mismatches = []
    reverse_matches = []
    for gen in ks.GEN_NAMES:
        for red in ks.RED_NAMES:
            a_base = worker_key(ks, gen, red, seed, a_nsym)
            page_base = ks.make_ks(gen, red, seed, d_page_nsym)
            book_base = ks.make_ks(gen, red, seed, d_book_nsym)
            if (a_base[:head_len] != page_base[:head_len] or
                a_base[:head_len] != book_base[:head_len]):
                forward_mismatches.append(f"{gen}|{red}")
            if (a_base[::-1][:head_len] == page_base[::-1][:head_len] or
                a_base[::-1][:head_len] == book_base[::-1][:head_len]):
                reverse_matches.append(f"{gen}|{red}")
    return {"schema": "b04-a-to-d-head-continuity-audit-v1",
            "source_revision": R.PIN, "source_hashes": hashes,
            "stage_a_merged_sha256": R.sha(stage_a_merged),
            "source_ciphertext_lengths": {"A_head": head_len,
                                          "D_page0": len(page[1]),
                                          "D_book": len(book[1])},
            "head_cipher_sha256": digest_symbols(head[1]),
            "page0_head_cipher_sha256": digest_symbols(page[1][:head_len]),
            "book_head_cipher_sha256": digest_symbols(book[1][:head_len]),
            "top_a_configuration": {k: top[k] for k in
                                    ("seed_hex", "gen", "red", "sign",
                                     "atbash", "dir", "offset", "score")},
            "source_requested_key_lengths": {"A_worker": a_nsym,
                                             "D_page0": d_page_nsym,
                                             "D_book": d_book_nsym},
            "source_key_lengths": {"A_worker": len(a_key),
                                   "D_page0": len(page_key),
                                   "D_book": len(book_key)},
            "source_key_first120_sha256": {
                "A_worker": digest_symbols(a_key[:head_len]),
                "D_page0": digest_symbols(page_key[:head_len]),
                "D_book": digest_symbols(book_key[:head_len])},
            "head_decodes_with_respective_length_keys": head_decodes,
            "forward_generators_reductions_checked": len(ks.GEN_NAMES) * len(ks.RED_NAMES),
            "forward_prefix_mismatches": forward_mismatches,
            "reverse_prefix_matches_in_either_D_length": reverse_matches,
            "scope_limit": "One frozen seed across every generator/reduction; no full Stage D decode was run."}


if __name__ == "__main__":
    source = pathlib.Path(
        "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301")
    stage_a = pathlib.Path(
        "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/b04-lp2-A-20261023/merged.json")
    result = audit(source, stage_a)
    output = HERE / "stage-continuity-audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                 indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output),
                      "forward_mismatches": len(result["forward_prefix_mismatches"]),
                      "reverse_prefix_matches": len(result["reverse_prefix_matches_in_either_D_length"]),
                      "head_scores": {k: v["score"] for k, v in
                                      result["head_decodes_with_respective_length_keys"].items()}},
                     sort_keys=True))
