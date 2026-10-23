"""Synthetic-only Stage D checkpoint, source parity and padding-probe tests."""
import json
import pathlib
import tempfile
import hashlib
import sys

import resumable_d as D
SOURCE = pathlib.Path(
    "C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work/source-cache/dukotah-cicada3301")


def test():
    H, _, ks, sk, _ = D.R.load_source(SOURCE)
    priors, segments = D.synthetic_inputs(H, sk)
    picks = D.select_picks(priors)
    assert len(picks) == 2
    assert picks[0]["gen"] == "sha256_ctr" and picks[1]["gen"] == "sha512_ctr"
    for si, segment in enumerate(segments):
        for pi, row in enumerate(picks):
            got, audit = D.decode_cell(row, segment, H, ks, sk)
            c0, c1 = segment[1:]
            native = len(c0) + row["offset"] + 512
            key = ks.make_ks(row["gen"], row["red"],
                             bytes.fromhex(row["seed_hex"]), native)
            direct = sk.beam_decode(c0 if row["atbash"] == 0 else c1,
                                    key, sign=row["sign"], o=row["offset"],
                                    beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
            assert got["score"] == direct["score"]
            assert got["text"] == direct["translit"][:96]
            assert audit["final_pointer"] == direct["ptr_end"]
            assert audit["decoded_runes"] == len(direct["plain_idx"])
            assert not audit["source_zero_padding_read"]

    # Exercise reversal, offset, sign, Atbash and rejection reduction together.
    reversed_row = {**picks[0], "red": "rej29", "sign": 1,
                    "atbash": 1, "dir": "rev", "offset": 4}
    got, audit = D.decode_cell(reversed_row, segments[1], H, ks, sk)
    c0, c1 = segments[1][1:]
    native = len(c0) + reversed_row["offset"] + 512
    key = ks.make_ks(reversed_row["gen"], reversed_row["red"],
                     bytes.fromhex(reversed_row["seed_hex"]), native)[::-1]
    direct = sk.beam_decode(c1, key, sign=1, o=4,
                            beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    assert got["score"] == direct["score"]
    assert got["text"] == direct["translit"][:96]
    assert audit["final_pointer"] == direct["ptr_end"]

    # Force the source decoder's own +[0] branch with short supplied key.
    cipher = sk.eng_to_idx("THEPRIMESARESACRED")[:8]
    short_key = [1, 2]
    observed = D.ObservedKey(short_key, len(short_key))
    traced = sk.beam_decode(cipher, observed, sign=-1,
                            beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    ordinary = sk.beam_decode(cipher, short_key, sign=-1,
                              beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    assert traced == ordinary
    assert observed.reads["extension_count"] == 1
    assert observed.reads["padded_read_count"] > 0

    with tempfile.TemporaryDirectory(prefix="b04-d-test-") as temp:
        out = pathlib.Path(temp)
        first = D.execute(SOURCE, out, synthetic=True, max_cells=1)
        assert not first["complete"] and first["cells_saved"] == 1
        first_cell = out / "cell-00-000.json"
        original = first_cell.read_bytes()
        final = D.execute(SOURCE, out, synthetic=True)
        assert final["complete"] and final["cells_saved"] == 4
        assert first_cell.read_bytes() == original
        again = D.execute(SOURCE, out, synthetic=True)
        assert again["complete"] and first_cell.read_bytes() == original
        merged = json.loads((out / "merged.json").read_text(encoding="utf-8"))
        assert merged["source_stage_summaries"] == final["source_stage_summaries"]
        parallel_out = out / "parallel"
        parallel = D.execute(SOURCE, parallel_out, synthetic=True, nproc=2)
        assert parallel["complete"] and parallel["cells_saved"] == 4
        assert (out / "manifest.json").read_bytes() == (parallel_out / "manifest.json").read_bytes()
        for serial_cell in out.glob("cell-*.json"):
            assert serial_cell.read_bytes() == (parallel_out / serial_cell.name).read_bytes()
        assert parallel["source_stage_summaries"] == final["source_stage_summaries"]
        assert parallel["cells_reading_padded_zero"] == final["cells_reading_padded_zero"]
        corrupt = json.loads(first_cell.read_text(encoding="utf-8"))
        corrupt["payload"]["source_row"]["score"] += 1.0
        D.R.atomic_json(first_cell, corrupt)
        try:
            D.execute(SOURCE, out, synthetic=True)
        except ValueError as error:
            assert "invalid Stage D checkpoint" in str(error)
        else:
            raise AssertionError("tampered Stage D checkpoint was accepted")
    return {"synthetic_cells": 4, "source_parity": True,
            "reverse_offset_atbash_reduction_parity": True,
            "resume_exact": True, "one_vs_two_workers_exact": True,
            "tamper_rejected": True,
            "padded_zero_read_detected": True}


if __name__ == "__main__":
    result = test()
    if "--write-receipt" in sys.argv:
        root = pathlib.Path(__file__).resolve().parent
        result.update({"schema": "b04-stage-d-synthetic-test-receipt-v1",
                       "source_revision": D.R.PIN,
                       "test_script_sha256": hashlib.sha256(
                           pathlib.Path(__file__).read_bytes()).hexdigest(),
                       "wrapper_sha256": hashlib.sha256(
                           (root / "resumable_d.py").read_bytes()).hexdigest(),
                       "real_stage_d_executed": False})
        out = root / "d-synthetic-test-receipt.json"
        out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                  indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
