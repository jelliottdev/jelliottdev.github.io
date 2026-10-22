"""Independent small oracle for the LP2-40 source arithmetic audit."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def prime(n):
    if n < 2:
        return False
    for divisor in range(2, n):
        if n % divisor == 0:
            return False
    return True


def main():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    first_line = (ROOT / "text/lp2-40.txt").read_text(encoding="utf-8").splitlines()[0]
    visible = "".join(first_line.split("-")[:2])
    assert len(visible) == len(result["rows"]) == 8
    for i, row in enumerate(result["rows"]):
        assert row["position"] == i + 1
        assert row["archived_cipher_rune"] == visible[i]
        target = next(j for j, item in enumerate(alphabet) if item["rune"] == visible[i])
        assert row["archived_cipher_index"] == target
        p = plan["source_crib_indices"][i]
        assert row["proposed_plaintext_index"] == p
        if i == 0:
            assert row["shifted_index"] is None
            assert row["atbash_index"] == row["prime_minus_one_step"] == 0
        else:
            # Reflect after shifting: 28 - (p + 18), considered modulo 29.
            shifted = (p + 18) % 29
            reflected = (28 - shifted) % 29
            step = alphabet[i-1]["prime"] - 1
            assert row["shifted_index"] == shifted
            assert row["atbash_index"] == reflected
            assert row["prime_minus_one_step"] == step
        computed = (row["atbash_index"] + row["prime_minus_one_step"]) % 29
        assert row["fixed_intermediate_index"] == computed
        assert row["fixed_match"] == (computed == target)
        assert row["required_residual_mod_29"] == (target - computed) % 29
        assert (row["source_signed_residual"] - row["required_residual_mod_29"]) % 29 == 0
    assert result["fixed_matches_all_eight"] == 1
    assert result["fixed_matches_non_f"] == 0
    for label, positions in (("FOR", range(3)), ("EVERY", range(3, 8)), ("FOR EVERY", range(8))):
        total = sum(alphabet[plan["source_crib_indices"][i]]["prime"] for i in positions)
        assert result["gp_sums"][label] == {"gp_prime_sum": total, "is_prime": prime(total)}
    print("PASS: independently checked source runes, 8 arithmetic rows, residuals and GP sums")


if __name__ == "__main__":
    main()
