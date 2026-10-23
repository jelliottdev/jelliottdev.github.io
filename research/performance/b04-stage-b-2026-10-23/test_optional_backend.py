"""Frozen synthetic campaign tests for the optional Stage D prefix backend."""
from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile

import resumable_d as D

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parents[3] / "source-cache" / "dukotah-cicada3301"
PLAN = HERE / "optional-backend-fixture-plan.json"
EXPECTED_PLAN_SHA256 = "7a4422c7f5163f53a8da2708e64f783d25bc695e822572bca0fe00f323eeafdd"


def expect_rejected(call, fragment):
    try:
        call()
    except ValueError as error:
        assert fragment in str(error), error
    else:
        raise AssertionError(f"expected refusal: {fragment}")


def direct_case(sk, cipher, key, kwargs):
    values = []
    for backend in D.BACKENDS:
        observed = D.ObservedKey(key, len(key))
        if backend == "source":
            result = sk.beam_decode(cipher, observed, **kwargs)
        else:
            result = D.backend_decoder(backend)(cipher, observed, gp=sk.gp,
                                                 Q=sk.Q, **kwargs)
        values.append((result, observed.reads))
    assert values[0] == values[1]
    return values[0][1]


def main():
    assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == EXPECTED_PLAN_SHA256
    H, _, ks, sk, hashes = D.R.load_source(SOURCE)
    priors, segments = D.synthetic_inputs(H, sk)
    picks = D.select_picks(priors)
    assert len(picks) == 2 and len(segments) == 2
    for segment in segments:
        for row in picks:
            a = D.decode_cell(row, segment, H, ks, sk, "source")
            b = D.decode_cell(row, segment, H, ks, sk, "prefix_shared")
            assert a == b

    altered = {**picks[0], "red": "rej29", "sign": 1, "atbash": 1,
               "dir": "rev", "offset": 4}
    assert D.decode_cell(altered, segments[1], H, ks, sk, "source") == \
           D.decode_cell(altered, segments[1], H, ks, sk, "prefix_shared")
    padded = direct_case(sk, sk.eng_to_idx("THEPRIMESARESACRED")[:8], [1, 2],
                         {"sign": -1, "beam_w": H.BEAM_W, "max_skip": H.MAX_SKIP})
    assert padded["extension_count"] == 1 and padded["padded_read_count"] > 0
    tied = direct_case(sk, [0] * 18, [0] * 600,
                       {"sign": -1, "beam_w": H.BEAM_W, "max_skip": H.MAX_SKIP})
    assert tied["read_count"] > 0

    with tempfile.TemporaryDirectory(prefix="b04-optional-backend-") as tmp:
        root = pathlib.Path(tmp)
        outputs = {}
        fresh_four_worker_seconds = {}
        for backend in D.BACKENDS:
            out = root / backend
            partial = D.execute(SOURCE, out, synthetic=True, max_cells=1,
                                backend=backend)
            assert partial["cells_saved"] == 1 and not partial["complete"]
            first = (out / "cell-00-000.json").read_bytes()
            final = D.execute(SOURCE, out, synthetic=True, nproc=4,
                              backend=backend)
            assert final["complete"] and final["cells_saved"] == 4
            assert (out / "cell-00-000.json").read_bytes() == first
            repeated = D.execute(SOURCE, out, synthetic=True, backend=backend)
            assert repeated["source_stage_summaries"] == final["source_stage_summaries"]
            assert (out / "cell-00-000.json").read_bytes() == first
            parallel = root / (backend + "-fresh-four")
            four = D.execute(SOURCE, parallel, synthetic=True, nproc=4,
                             backend=backend)
            fresh_four_worker_seconds[backend] = four["elapsed_this_invocation_s"]
            assert four["decoder_backend"] == backend
            assert four["source_stage_summaries"] == final["source_stage_summaries"]
            serial = root / (backend + "-fresh-one")
            one = D.execute(SOURCE, serial, synthetic=True, nproc=1,
                            backend=backend)
            assert one["source_stage_summaries"] == four["source_stage_summaries"]
            for cell in out.glob("cell-*.json"):
                assert cell.read_bytes() == (parallel / cell.name).read_bytes()
                assert cell.read_bytes() == (serial / cell.name).read_bytes()
            outputs[backend] = (out, final)

        source_out, source_final = outputs["source"]
        fast_out, fast_final = outputs["prefix_shared"]
        assert source_final["source_stage_summaries"] == fast_final["source_stage_summaries"]
        assert source_final["cells_reading_padded_zero"] == fast_final["cells_reading_padded_zero"]
        source_man = json.loads((source_out / "manifest.json").read_text())
        fast_man = json.loads((fast_out / "manifest.json").read_text())
        assert source_man["manifest_sha256"] != fast_man["manifest_sha256"]
        assert source_man["source_hashes"] == fast_man["source_hashes"] == hashes
        assert fast_man["decoder_backend"]["implementation_sha256"] == D.R.sha(D.FAST_BACKEND)
        assert source_man["decoder_backend"]["wrapper_sha256"] == D.R.sha(pathlib.Path(D.__file__))
        for name in ("cell-00-000.json", "cell-00-001.json", "cell-01-000.json",
                     "cell-01-001.json"):
            a = json.loads((source_out / name).read_text())["payload"]
            b = json.loads((fast_out / name).read_text())["payload"]
            assert a["source_row"] == b["source_row"]
            assert a["key_access_audit"] == b["key_access_audit"]
            assert a["manifest_sha256"] != b["manifest_sha256"]

        expect_rejected(lambda: D.execute(SOURCE, source_out, synthetic=True,
                                          backend="prefix_shared"), "manifest changed")
        changed = dict(fast_man)
        changed["decoder_backend"] = dict(changed["decoder_backend"])
        changed["decoder_backend"]["implementation_sha256"] = "0" * 64
        D.R.atomic_json(fast_out / "manifest.json", changed)
        expect_rejected(lambda: D.execute(SOURCE, fast_out, synthetic=True,
                                          backend="prefix_shared"), "manifest changed")
        changed["decoder_backend"]["implementation_sha256"] = fast_man["decoder_backend"]["implementation_sha256"]
        changed["decoder_backend"]["wrapper_sha256"] = "f" * 64
        D.R.atomic_json(fast_out / "manifest.json", changed)
        expect_rejected(lambda: D.execute(SOURCE, fast_out, synthetic=True,
                                          backend="prefix_shared"), "manifest changed")
        D.R.atomic_json(fast_out / "manifest.json", fast_man)
        cell = fast_out / "cell-00-000.json"
        corrupt = json.loads(cell.read_text())
        corrupt["payload"]["source_row"]["score"] += 1
        D.R.atomic_json(cell, corrupt)
        expect_rejected(lambda: D.execute(SOURCE, fast_out, synthetic=True,
                                          backend="prefix_shared"), "invalid Stage D checkpoint")

    receipt = {"schema": "b04-stage-d-optional-backend-test-v1",
               "fixture_plan_sha256": EXPECTED_PLAN_SHA256,
               "wrapper_sha256": D.R.sha(pathlib.Path(D.__file__)),
               "prototype_sha256": D.R.sha(D.FAST_BACKEND),
               "source_revision": D.R.PIN, "synthetic_cells_per_backend": 4,
               "complete_cell_rows_and_key_reads_equal": True,
               "summary_semantics_equal": True, "stable_tie_equal": True,
               "actual_source_padding_reads_equal": True,
               "four_workers_and_resume_equal": True,
               "fresh_four_worker_seconds_descriptive": fresh_four_worker_seconds,
               "cross_backend_and_tampered_cache_rejected": True,
               "real_stage_d_executed": False}
    (HERE / "optional-backend-test-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
