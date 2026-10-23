"""Replay the pinned Campaign VII reading-direction grid and added controls."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "analysis" / "campaign7" / "reading_direction.py"
RESULT = HERE / "results.json"


def load_source():
    spec = importlib.util.spec_from_file_location("pinned_reading_direction", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_grid(mod, pages, include_readings=False):
    best = (-999.0, None)
    per_order = {}
    page_best = []
    count = 0
    digest = hashlib.sha256()
    for page_no, lines in enumerate(pages):
        local = (-999.0, None)
        for order, runes in mod.orders(lines):
            for cipher, plain in mod.cipher_suite(runes):
                text = mod.gp.indices_to_translit(plain)
                score = mod.SC.score_norm(text)
                count += 1
                digest.update(f"{page_no}|{order}|{cipher}|{score:.12f}|".encode())
                digest.update(bytes(plain))
                rec = {"source_page": page_no, "order": order,
                       "cipher": cipher, "score": score, "preview": text[:70]}
                if score > best[0]:
                    best = (score, rec)
                if score > local[0]:
                    local = (score, rec)
                if score > per_order.get(order, -999.0):
                    per_order[order] = score
        if include_readings:
            page_best.append(local[1])
    return {"best": best[1], "per_order_best": per_order,
            "candidate_count": count, "grid_sha256": digest.hexdigest(),
            "page_best": page_best if include_readings else None}


def positive_controls(mod, pages):
    solved = []
    for source_page, lines in enumerate(pages[-2:], len(pages)-2):
        plain = [x for row in lines for x in row]
        solved.append({"source_page": source_page,
                       "score": mod.SC.score_norm(mod.gp.indices_to_translit(plain)),
                       "runes": len(plain)})
    assert any(x["score"] > -5 for x in solved), "original solved-page gate failed"
    lines = pages[-1]
    direct = [x for row in lines for x in row]
    target = mod.SC.score_norm(mod.gp.indices_to_translit(direct))
    assert target > -5, "planted page cannot clear source threshold"
    # Odd rows are reversed twice: once during construction, once by the
    # source's boustrophedon route.  Source shift7 subtracts the planted +7.
    planted_boustro = [[(x+7) % 29 for x in (row if i % 2 == 0 else row[::-1])]
                       for i, row in enumerate(lines)]
    recovered = dict(mod.orders(planted_boustro))["boustro"]
    decoded = dict(mod.cipher_suite(recovered))["shift7"]
    assert decoded == direct
    # Put the solved stream into each ordinal column in source traversal
    # order, then encode every position by the same shift.
    lens = [len(row) for row in lines]
    col_rows = [[None] * n for n in lens]
    t = iter(direct)
    for col in range(max(lens)):
        for row in col_rows:
            if col < len(row):
                row[col] = (next(t) + 7) % 29
    recovered_col = dict(mod.orders(col_rows))["colmajor"]
    decoded_col = dict(mod.cipher_suite(recovered_col))["shift7"]
    assert decoded_col == direct
    return {"solved_pages": solved, "plant_score": target,
            "plant_runes": len(direct), "boustro_shift7_exact": True,
            "colmajor_shift7_exact": True,
            "positive_threshold": -5.0}


def source_pages(mod):
    pages = mod.line_pages()
    assert len(pages) == 57, len(pages)
    assert sum(len(row) for p in pages[:55] for row in p) == 12956
    return pages


def shuffled_pages(pages, rng):
    out = []
    for lines in pages:
        lengths = [len(row) for row in lines]
        flat = [x for row in lines for x in row]
        rng.shuffle(flat)
        cursor = 0
        next_lines = []
        for length in lengths:
            next_lines.append(flat[cursor:cursor+length]); cursor += length
        assert cursor == len(flat)
        out.append(next_lines)
    return out


def compute():
    mod = load_source()
    pages = source_pages(mod)
    positive = positive_controls(mod, pages)
    print("Positive controls passed: solved tails, boustrophedon and column plants", flush=True)
    real = score_grid(mod, pages[:55], include_readings=True)
    all_pages = score_grid(mod, pages, include_readings=False)
    assert real["candidate_count"] == 10175
    assert all_pages["candidate_count"] == 10545
    original = json.loads((HERE / "source/analysis/campaign7/reading_direction_results.json").read_text())
    assert round(real["best"]["score"], 3) == original["best_unsolved"]["score"]
    assert real["best"]["source_page"] == original["best_unsolved"]["page"]
    assert real["best"]["order"] == original["best_unsolved"]["order"]
    assert real["best"]["cipher"] == original["best_unsolved"]["cipher"]
    assert round(all_pages["best"]["score"], 3) == original["best_all"]["score"]
    assert all_pages["best"]["source_page"] == original["best_all"]["page"]
    for order, score in all_pages["per_order_best"].items():
        assert round(score, 3) == original["per_order_best"][order]
    print("Archived source winner and per-route score parity passed", flush=True)
    rng = random.Random(3301)
    controls = []
    for i in range(49):
        null = score_grid(mod, shuffled_pages(pages[:55], rng))
        controls.append({"replicate": i, "best_score": null["best"]["score"],
                         "best_source_page": null["best"]["source_page"],
                         "best_order": null["best"]["order"],
                         "best_cipher": null["best"]["cipher"],
                         "candidate_count": null["candidate_count"],
                         "grid_sha256": null["grid_sha256"]})
        print(f"null {i+1}/49: {null['best']['score']:.4f}", flush=True)
    observed = real["best"]["score"]
    return {"schema": "liberpedia-direction-cipher-grid-results-v1",
            "positive_controls": positive,
            "real": real,
            "source_all_pages": {k:v for k,v in all_pages.items() if k != "page_best"},
            "source_parity": "all archived summary fields matched after source three-decimal rounding",
            "null_controls": controls,
            "null_at_least_observed": sum(x["best_score"] >= observed for x in controls),
            "null_count": len(controls)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fresh = compute()
    if args.check:
        assert fresh == json.loads(RESULT.read_text(encoding="utf8"))
        print("PASS complete saved result")
    else:
        RESULT.write_text(json.dumps(fresh, ensure_ascii=False, indent=2)+"\n", encoding="utf8", newline="\n")
        print("Saved", RESULT)
