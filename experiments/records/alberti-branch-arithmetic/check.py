"""Independent oracle for the Alberti source-arithmetic report."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    out = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    source = plan["inputs"][0]
    assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    row = (ROOT / source["path"]).read_text(encoding="utf-8").splitlines()[7]
    # An independent punctuation split: do not import the producer's parser.
    segments = row.rstrip("/").replace(".", "-").split("-")
    assert [len(s) for s in segments] == [3, 4, 6, 5, 1]
    assert all(all(0x16A0 <= ord(ch) <= 0x16FF for ch in s) for s in segments)
    assert out["runes_per_segment"] == [3, 4, 6, 5, 1]
    numbers = plan["arithmetic"]
    add = sum(numbers["short_overlay"])
    assert add == -25
    for side in ("left", "right"):
        plant = numbers[f"plant_{side}"]
        final = numbers[f"reported_{side}_final"]
        groups = [plant[0:4], plant[4:9], plant[9:13]]
        assert [sum(x) for x in groups] == out[side]["plant_group_sums"]
        assert [sum(final[0:4]), sum(final[4:9]), sum(final[9:13])] == out[side]["posted_final_group_sums"]
        pair = [sum(groups[0]) + add, sum(groups[2]) + add]
        assert pair == numbers["reported_short_sums"][side] == out[side]["computed_short_sums"]
        assert [divmod(x, 31)[1] for x in pair] == out[side]["standard_short_residues"]
        assert len(out[side]["rotations"]) == 13
        for start, entry in enumerate(out[side]["rotations"]):
            shifted = [plant[(start + i) % 13] for i in range(13)]
            sums = [sum(shifted[:4]) + add, sum(shifted[9:]) + add]
            assert entry == {"start_zero_based": start, "raw_short_sums": sums,
                             "standard_mod_31": [divmod(x, 31)[1] for x in sums]}
    assert out["left"]["posted_final_group_sums"] == [-13, -15, -17]
    assert out["right"]["posted_final_group_sums"] == [-33, -15, -39]
    assert out["right"]["standard_short_residues"] == [29, 23]
    assert out["right_reported_residues"] == [2, 8]
    assert not out["right_residue_claim_matches_standard_modulo"]
    assert out["left_exact_raw_rotation_hits"] == [0]
    assert out["right_reported_residue_rotation_hits"] == []
    print("Independent Alberti row, sums, modulo, and 26 rotations check passed")


if __name__ == "__main__":
    main()
