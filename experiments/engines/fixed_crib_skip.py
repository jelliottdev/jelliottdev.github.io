"""Exact feasibility of a fixed GP29 plaintext prefix under key-skip decoding.

This is a constraint check, not an English-language scorer. It follows the
accepted-key and rejected-doublet rules in the pinned Dukotah skip decoder,
without the source decoder's beam pruning.
"""

from collections.abc import Sequence


def match_prefix(
    cipher: Sequence[int],
    plain: Sequence[int],
    key: Sequence[int],
    sign: int,
    max_skip: int = 3,
    skip_mode: str = "single",
) -> int:
    """Return the longest feasible fixed prefix, counting its first rune.

    A skipped key symbol is admissible only when it would emit the preceding
    ciphertext rune for the proposed *current* plaintext symbol.
    """
    if sign not in (-1, 1) or max_skip < 0 or skip_mode not in ("single", "pair"):
        raise ValueError("invalid sign, skip bound or mode")
    limit = min(len(cipher), len(plain))
    if not limit or not key or (cipher[0] + sign * key[0]) % 29 != plain[0]:
        return 0
    positions = {0}
    for i in range(1, limit):
        next_positions: set[int] = set()
        ci, pi, previous = cipher[i], plain[i], cipher[i - 1]
        for pa in positions:
            for skipped in range(0, max_skip + 1, 2 if skip_mode == "pair" else 1):
                accepted = pa + skipped + 1
                if accepted >= len(key):
                    break
                if (ci + sign * key[accepted]) % 29 != pi:
                    continue
                discarded = (range(pa + 1, accepted, 2) if skip_mode == "pair"
                             else range(pa + 1, accepted))
                if all(
                    (pi - sign * key[unused]) % 29 == previous
                    for unused in discarded
                ):
                    next_positions.add(accepted)
        if not next_positions:
            return i
        positions = next_positions
    return limit
