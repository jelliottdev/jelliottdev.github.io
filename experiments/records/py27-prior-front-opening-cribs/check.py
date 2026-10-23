"""Independent full-grid and planted-control check for the L3 fixed cribs."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "source"))
import gen_py27  # noqa: E402


def words_from_source():
    source = json.loads((HERE / "source/seedprior20.json").read_text(encoding="utf-8"))
    used = set()
    words = []
    for row in source["order"]:
        value = int(row["seed"]) & 0xFFFFFFFF
        if value not in used:
            used.add(value)
            words.append(value)
    for row in source["order"][:64]:
        center = int(row["seed"])
        for delta in range(-512, 513):
            value = (center + delta) & 0xFFFFFFFF
            if value not in used:
                used.add(value)
                words.append(value)
    assert len(words) == 45975
    assert hashlib.sha256("".join(f"{w}\n" for w in words).encode()).hexdigest() == "061eb4dc5c72d4623d9350358bbbb8e545194602c39d0c5d98109c23f31772f3"
    return words


def source_key(word, reducer, machine):
    if machine == "i386":
        init = [word & 0xFFFFFFFF]
    else:
        product = (word * 0x9E3779B97F4A7C15) % (1 << 64)
        init = [product % (1 << 32), product // (1 << 32)]
    mt = gen_py27.MT19937()
    mt.init_by_array(init)
    return gen_py27.REDUCERS[reducer](mt, 45)


def possible_prefix(cipher, plain, key):
    """All admissible accepted-key positions, without English-score pruning."""
    if not cipher or len(cipher) != len(plain) or (cipher[0] - key[0]) % 29 != plain[0]:
        return 0
    positions = {0}
    for i in range(1, len(plain)):
        next_positions = set()
        for last in positions:
            for skipped in range(4):
                take = last + 1 + skipped
                if take >= len(key) or (cipher[i] - key[take]) % 29 != plain[i]:
                    continue
                if all((plain[i] + key[j]) % 29 == cipher[i - 1]
                       for j in range(last + 1, take)):
                    next_positions.add(take)
        if not next_positions:
            return i
        positions = next_positions
    return len(plain)


def brute_prefix(cipher, plain, key):
    if (cipher[0] - key[0]) % 29 != plain[0]:
        return 0

    def walk(i, last):
        if i >= len(plain):
            return i
        best = i
        for skipped in range(4):
            take = last + skipped + 1
            if take >= len(key) or (cipher[i] - key[take]) % 29 != plain[i]:
                continue
            if all((plain[i] + key[j]) % 29 == cipher[i - 1]
                   for j in range(last + 1, take)):
                best = max(best, walk(i + 1, take))
        return best

    return walk(1, 0)


def controls():
    mt = gen_py27.MT19937()
    mt.init_by_array([0x123, 0x234, 0x345, 0x456])
    assert [mt.genrand_uint32() for _ in range(5)] == [1067595299, 955945823, 477289528, 4107218783, 4228976476]
    plain = [24, 7, 24, 4, 9, 21, 17, 18, 4, 7, 0, 10]
    for name, reducer, machine in (
        ("grb5_mod_i386", "grb5_mod", "i386"),
        ("grb5_rej_i386", "grb5_rej", "i386"),
        ("shuffle29_i386", "shuffle29", "i386"),
        ("random29_amd64", "random29", "amd64"),
    ):
        key = source_key(1325734783, reducer, machine)
        cipher = [(p + k) % 29 for p, k in zip(plain, key)]
        assert possible_prefix(cipher, plain, key) == 12, name
    key = [5, (plain[0] + 5 - plain[1]) % 29, 7] + [8] * 20
    cipher = [(plain[0] + key[0]) % 29, (plain[1] + key[2]) % 29]
    cipher.extend((p + 8) % 29 for p in plain[2:])
    assert possible_prefix(cipher, plain, key) == 12  # forced collision skip
    rng = random.Random(20261023)
    for _ in range(400):
        p = [rng.randrange(29) for _ in range(5)]
        k = [rng.randrange(29) for _ in range(22)]
        c = [rng.randrange(29) for _ in range(5)]
        c[0] = (p[0] + k[0]) % 29
        assert possible_prefix(c, p, k) == brute_prefix(c, p, k)


def check():
    controls()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    words = words_from_source()
    alphabet = {a["rune"]: a["index"] for a in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}
    target_by_first = defaultdict(list)
    for page_id in result["pages"]:
        raw = json.loads((ROOT / "data/pages" / f"{page_id}.json").read_text(encoding="utf-8"))["raw"]
        cipher = tuple(alphabet[r] for r in raw if r in alphabet)[:12]
        for crib in result["cribs"]:
            plain = tuple(crib["indices"])
            target_by_first[(cipher[0] - plain[0]) % 29].append((page_id, crib["id"], cipher, plain))
    histogram = Counter()
    by_config = defaultdict(Counter)
    unique = set()
    exact = []
    leading = []
    digest = hashlib.sha256()
    for name, reducer, machine in (
        ("grb5_mod_i386", "grb5_mod", "i386"),
        ("grb5_rej_i386", "grb5_rej", "i386"),
        ("shuffle29_i386", "shuffle29", "i386"),
        ("random29_amd64", "random29", "amd64"),
    ):
        for at, word in enumerate(words):
            key = source_key(word, reducer, machine)
            unique.add(bytes(key))
            best = 0
            matches = []
            for page_id, crib_id, cipher, plain in target_by_first[key[0]]:
                length = possible_prefix(cipher, plain, key)
                best = max(best, length)
                if length == 12:
                    matches.append([page_id, crib_id])
            histogram[best] += 1
            by_config[name][best] += 1
            if matches:
                exact.append({"config": name, "word_index": at, "word": word,
                              "matches": matches})
            if best >= 7 and len(leading) < 100:
                leading.append({"config": name, "word_index": at, "word": word,
                                "prefix": best})
            digest.update((json.dumps([name, at, word, best, matches], separators=(",", ":")) + "\n").encode())
        print("Checked", name, flush=True)
    assert result["word_count"] == len(words) == 45975
    assert result["rows"] == sum(histogram.values()) == 183900
    assert result["distinct_first_45_symbol_streams"] == len(unique)
    assert result["best_prefix_histogram"] == {str(k): histogram[k] for k in sorted(histogram)}
    assert result["per_config"] == {c: {str(k): v[k] for k in sorted(v)} for c, v in by_config.items()}
    assert result["exact_matches"] == exact and result["long_prefix_examples"] == leading
    assert result["case_digest_sha256"] == digest.hexdigest()
    print("Full 183,900-case independent check passed")


if __name__ == "__main__":
    check()
