"""Replay the pinned P25 Liber AL coarse/refine source rule on corrected page 25.

The public source checkout is an external input: no source text or corpus is
redistributed in this experiment. Paths relocated by the source repository are
restored in a temporary directory without changing source functions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(repo: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{PLAN['source']['commit']}:{path}"])


def source(repo: Path):
    paths = {
        "script": PLAN["source"]["script_path"],
        "page": PLAN["source_inputs"]["source_page_path"],
        "corpus": PLAN["source_inputs"]["corpus_pinned_path"],
    }
    payloads = {name: git_bytes(repo, path) for name, path in paths.items()}
    expected = {
        "script": PLAN["source"]["script_sha256"],
        "page": PLAN["source_inputs"]["source_page_sha256"],
        "corpus": PLAN["source_inputs"]["corpus_sha256"],
    }
    for name, data in payloads.items():
        assert sha(data) == expected[name], f"pinned {name} byte mismatch"
    return payloads


def load_source(payloads: dict[str, bytes], temp: Path):
    page_path = temp / "pages" / "page_25" / "runes.txt"
    corpus_path = temp / "reference" / "liber_al_vel_legis.txt"
    page_path.parent.mkdir(parents=True)
    corpus_path.parent.mkdir(parents=True)
    page_path.write_bytes(payloads["page"])
    corpus_path.write_bytes(payloads["corpus"])
    env = {"__file__": "p25_liberal_offset_sweep.py", "__name__": "pinned_source"}
    exec(compile(payloads["script"], "p25_liberal_offset_sweep.py", "exec"), env)
    env["PAGES_DIR"] = temp / "pages"
    env["REF"] = temp / "reference"
    cipher = env["load_page_indices"](25)
    key = env["load_liber_al_indices"]()
    assert len(cipher) == 255 and len(key) >= 5255
    return env, cipher, key


def search(env: dict, cipher: list[int], source_key: list[int]):
    """Preserve all candidate and tuple-sort semantics from source main()."""
    n = len(cipher)
    repeated = source_key * (((n + len(source_key) - 1) // len(source_key)) + 1)

    def row(off: int, mode: str):
        key = repeated[off : off + n]
        plain = env["decrypt_with_key"](cipher, key, mode)
        text = env["indices_to_runeglish"](plain)
        return (env["trigram_score"](text), env["compute_ioc"](plain), off, mode, text[:200])

    coarse = [row(off, mode) for off in range(0, 5001, 100) for mode in ("beaufort", "sub")]
    selected = sorted(coarse, reverse=True)[:6]
    offsets = sorted({o for _, _, off, _, _ in selected for o in range(max(0, off - 200), off + 201)})
    refined = [row(off, mode) for off in offsets for mode in ("beaufort", "sub")]
    all_rows = sorted(coarse + refined, reverse=True)
    return {
        "coarse_top_six": selected,
        "refined_offset_count": len(offsets),
        "evaluated_rows": len(all_rows),
        "top_100": all_rows[:100],
        "max_score": all_rows[0][0],
        "all_rows_sha256": sha(json.dumps(all_rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
    }


def plant(env: dict, key: list[int], off: int, mode: str, n: int):
    plain = ([2, 18, 24, 9, 23] * ((n + 4) // 5))[:n]
    segment = key[off : off + n]
    if mode == "beaufort":
        cipher = [(k - p) % 29 for p, k in zip(plain, segment)]
    else:
        cipher = [(p + k) % 29 for p, k in zip(plain, segment)]
    assert env["decrypt_with_key"](cipher, segment, mode) == plain
    return cipher, plain


def run_controls(env: dict, key: list[int], n: int):
    receipts = []
    for off in (300, 1700, 137):
        for mode in ("beaufort", "sub"):
            cipher, plain = plant(env, key, off, mode, n)
            outcome = search(env, cipher, key)
            rows = outcome["top_100"]
            matches = [r for r in rows if r[2] == off and r[3] == mode]
            if off in (300, 1700):
                assert matches, f"planted {off}/{mode} absent from selected top 100"
                expected = env["trigram_score"](env["indices_to_runeglish"](plain))
                assert matches[0][0] == expected
            receipts.append({"offset": off, "mode": mode, "found_in_top_100": bool(matches), "score": matches[0][0] if matches else None, "best_score": outcome["max_score"]})
    return receipts


def build(repo: Path, controls_only: bool = False):
    payloads = source(repo)
    with tempfile.TemporaryDirectory(prefix="liberpedia-p25-") as td:
        env, cipher, key = load_source(payloads, Path(td))
        controls = run_controls(env, key, len(cipher))
        base = {"schema": "liberpedia-p25-offset-result-v1", "plan_sha256": sha((HERE / "plan.json").read_bytes()), "source_sha256": sha(payloads["script"]), "page_sha256": sha(payloads["page"]), "corpus_sha256": sha(payloads["corpus"]), "page": "lp2-08", "rune_count": len(cipher), "key_rune_count": len(key), "controls": controls}
        if controls_only:
            return base
        base["manuscript"] = search(env, cipher, key)
        rng = random.Random(20261023)
        nulls = []
        for i in range(199):
            shuffled = cipher.copy()
            rng.shuffle(shuffled)
            outcome = search(env, shuffled, key)
            nulls.append({"trial": i, "cipher_sha256": sha(bytes(shuffled)), "max_score": outcome["max_score"], "all_rows_sha256": outcome["all_rows_sha256"], "coarse_top_six": [r[2:4] for r in outcome["coarse_top_six"]], "evaluated_rows": outcome["evaluated_rows"]})
        base["order_control"] = {"count": len(nulls), "nulls": nulls, "at_least_manuscript": sum(x["max_score"] >= base["manuscript"]["max_score"] for x in nulls)}
        return base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--controls-only", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.source_repo, args.controls_only)
    path = HERE / ("controls.json" if args.controls_only else "results.json")
    raw = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert path.read_text(encoding="utf-8") == raw
        print(f"checked {path.name}")
    else:
        path.write_text(raw, encoding="utf-8", newline="\n")
        print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
