"""Read-only B-04 keyskip1/scorer control, separate from its large LP2 sweep.

Run from any cwd: python b04-shared-control-preflight.py --source-root PATH
Writes only --output. Requires pinned Dukotah f08b20b checkout.
"""
import argparse
import hashlib
import importlib
import json
import pathlib
import subprocess
import sys

PIN = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    args = ap.parse_args()
    root = args.source_root.resolve()
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise SystemExit(f"Expected pinned source {PIN}; found {head}")

    # Verify working inputs against pinned Git before importing executable source.
    for relative in ['liber-primus/analysis/round13/B04/control.py', 'liber-primus/analysis/round13/B04/ks.py', 'liber-primus/analysis/round13/B04/harness.py', 'liber-primus/analysis/campaign18_skip/skipdecode.py', 'liber-primus/src/lp/score.py', 'liber-primus/analysis/round13/B04/results_G1_rerun.json', 'liber-primus/analysis/round13/B04/results_gates.json']:
        pinned = subprocess.check_output(["git", "-C", str(root), "show", PIN + ":" + relative])
        if (root / relative).read_bytes() != pinned:
            raise SystemExit("Working input differs from pinned source: " + relative)

    b04 = root / "liber-primus" / "analysis" / "round13" / "B04"
    sys.path.insert(0, str(b04))
    ctl = importlib.import_module("control")
    sk = ctl.sk

    # Source G1 is small and invokes the source's actual scorer/beam, including
    # its own 200 shuffled-text scores. Do not run the 1.38M Stage-A gate here.
    g1 = ctl.gate_g1()

    # Full-message synthetic plant under a dictionary-resident source key.
    p = sk.eng_to_idx(ctl.PLAIN)
    klen = len(p) * (ctl.MAX_SKIP + 2) + 128
    key = ctl.ks.make_ks(ctl.PLANT_GEN, ctl.PLANT_RED, ctl.PLANT_SEED, klen)
    manual = []
    for counter in range((klen + 31) // 32):
        manual.extend(b % 29 for b in hashlib.sha256(
            ctl.PLANT_SEED + counter.to_bytes(4, "big")
        ).digest())
    assert key[:klen] == manual[:klen]
    cipher, skip_counts, used = sk.encipher_keyskip(
        p, key, sign=ctl.PLANT_SIGN, supp=0.83, seed=3301
    )
    decoded = sk.beam_decode(
        cipher, key, sign=ctl.PLANT_SIGN, o=0,
        beam_w=ctl.BEAM_W, max_skip=ctl.MAX_SKIP
    )
    rigid = sk.rigid_decode(cipher, key, sign=ctl.PLANT_SIGN, o=0)
    wrong = ctl.ks.make_ks(ctl.PLANT_GEN, ctl.PLANT_RED, b"WRONG", klen)
    wrong_decoded = sk.beam_decode(
        cipher, wrong, sign=ctl.PLANT_SIGN, o=0,
        beam_w=ctl.BEAM_W, max_skip=ctl.MAX_SKIP
    )

    # Independent algebraic check against every actual key index accepted by
    # the source encoder; this does not depend on beam search or English score.
    algebraic_plain = [(c + ctl.PLANT_SIGN * key[j]) % 29 for c, j in zip(cipher, used)]
    recovered = decoded["plain_idx"]
    exact = len(recovered) == len(p) and recovered == p
    assert sum(skip_counts) == used[-1] - (len(p) - 1)
    assert algebraic_plain == p
    assert len(cipher) == len(p)

    g1_pass = bool(g1["PASS"] and g1["beam_correct_seed"] >= -5.5
                   and g1["char_recovery"] >= .90
                   and g1["beam_correct_seed"] - g1["beam_wrong_seed"] > 1
                   and g1["rigid_correct_seed"] < -6)
    full_pass = bool(exact and decoded["score"] >= -5.5
                     and decoded["score"] - wrong_decoded["score"] > 1
                     and rigid["score"] < -6)

    source_files = [
        b04 / "control.py", b04 / "ks.py", b04 / "harness.py",
        root / "liber-primus" / "analysis" / "campaign18_skip" / "skipdecode.py",
        root / "liber-primus" / "src" / "lp" / "score.py",
        root / "liber-primus" / "analysis" / "round13" / "B04" / "results_G1_rerun.json",
        root / "liber-primus" / "analysis" / "round13" / "B04" / "results_gates.json",
    ]
    receipt = {
        "schema": "liberpedia-b04-shared-preflight-v1",
        "source_revision": head,
        "source_files": {str(x.relative_to(root)).replace('\\', '/'): sha(x) for x in source_files},
        "method": "Pinned source GP29 greedy transliteration; sha256_ctr/mod29 dictionary-resident key; sign -1; source encipher_keyskip(supp=.83, seed=3301); beam400 max_skip3; source English score_norm gate -5.5.",
        "g1_current_code": g1,
        "g1_current_code_pass": g1_pass,
        "full_message": {
            "plain_source": "control.py PLAIN (entire constant, not first 120/190 Latin chars)",
            "plain_runes": len(p),
            "cipher_runes": len(cipher),
            "skipped_key_values": sum(skip_counts),
            "max_skip_on_one_rune": max(skip_counts),
            "exact_all_runes": exact,
            "algebraic_check_exact_all_runes": algebraic_plain == p,
            "independent_sha256_counter_key_check": True,
            "source_score": decoded["score"],
            "wrong_key_score": wrong_decoded["score"],
            "rigid_correct_key_score": rigid["score"],
            "score_gate": -5.5,
            "full_message_gate_pass": full_pass,
            "plaintext_indices_sha256": hashlib.sha256(bytes(p)).hexdigest(),
            "ciphertext_indices_sha256": hashlib.sha256(bytes(cipher)).hexdigest(),
        },
        "archived_gate_note": "results_gates.json G1=false was an alias-field driver bug; GATE-NOTE.md and results_G1_rerun.json explicitly correct it. Current code returns G1 pass. Archived G2 Stage-A rank-1 is not rerun here.",
        "scope": "Supports B-04 keyskip1/English source decoder and exact-key planted recovery only. Does not validate nine-register I2, keyskip2/pair, drift, finite-offset prefilters, full Stage-A rank over 1.38M cases, or any LP2 negative.",
    }
    assert g1_pass and full_pass
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"g1_pass": g1_pass, "full_message_pass": full_pass,
                      "runes": len(p), "skips": sum(skip_counts),
                      "score": decoded["score"]}))


if __name__ == "__main__":
    main()
