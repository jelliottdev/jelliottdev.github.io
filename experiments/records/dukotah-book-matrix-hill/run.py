"""Retrospective Campaign VII Hill-matrix replay and a one-cell input sensitivity.

The archived source result is read as a receipt, never overwritten. A separate
199-trial whole-selection shuffle is a conditional comparison, not a cipher model.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = HERE / "source"
sys.path.insert(0, str(SRC / "src"))
sys.path.insert(0, str(SRC / "analysis"))
from lp import gematria as gp, score as score_module  # noqa: E402
from run_stats import load_pages  # noqa: E402

SCRIPT = SRC / "analysis/campaign7/hill5_magic.py"
ARCHIVED = SRC / "analysis/campaign7/hill5_magic_results.json"
OUT = HERE / "results.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_matrices():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    mats = next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "MATRICES" for t in node.targets))
    canonical = json.dumps(mats, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == json.loads((HERE / "plan.json").read_text())["matrix_json_sha256"]
    return mats


def inverse(matrix):
    n = len(matrix)
    a = [[v % 29 for v in row] + [int(i == j) for j in range(n)]
         for i, row in enumerate(matrix)]
    for c in range(n):
        pivot = next((r for r in range(c, n) if a[r][c] % 29), None)
        if pivot is None:
            return None
        a[c], a[pivot] = a[pivot], a[c]
        a[c] = [(v * pow(a[c][c], -1, 29)) % 29 for v in a[c]]
        for r in range(n):
            if r != c:
                factor = a[r][c]
                a[r] = [(a[r][j] - factor * a[c][j]) % 29 for j in range(2*n)]
    return [row[n:] for row in a]


def transpose(matrix):
    return [list(x) for x in zip(*matrix)]


def variants(matrix):
    m = [[v % 29 for v in row] for row in matrix]
    out = {"M": m, "MT": transpose(m)}
    inv = inverse(m)
    if inv is not None:
        out["Minv"] = inv
        out["MTinv"] = inverse(transpose(m))
    return out


def apply(stream, matrix):
    n = len(matrix)
    return [sum(matrix[r][c] * stream[i+c] for c in range(n)) % 29
            for i in range(0, len(stream)-n+1, n) for r in range(n)]


def source_replay():
    with tempfile.TemporaryDirectory(prefix="lp-hill-source-") as tmp:
        staged = Path(tmp) / "source"
        shutil.copytree(SRC, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        out = staged / "analysis/campaign7/hill5_magic_results.json"
        out.unlink(missing_ok=True)
        proc = subprocess.run([sys.executable, str(staged / "analysis/campaign7/hill5_magic.py")],
                              capture_output=True, text=True, encoding="utf-8", check=True)
        fresh = json.loads(out.read_text(encoding="utf-8"))
    archived = json.loads(ARCHIVED.read_text(encoding="utf-8"))
    assert fresh == archived, "source output differs from the archived result"
    return {"parity": True, "archived_sha256": sha(ARCHIVED),
            "fresh_result_sha256_canonical": hashlib.sha256(json.dumps(fresh,sort_keys=True).encode()).hexdigest(),
            "source_stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest()}


def pages_and_reading():
    pages = load_pages()
    assert len(pages) == 57 and len(pages[-2]) == 85
    ids = [f"lp2-{i:02}" for i in range(56) if i != 50]
    site = [gp.runes_to_indices(json.loads((ROOT / "data/pages" / (name + ".json")).read_text(encoding="utf-8"))["raw"])
            for name in ids]
    assert pages[:55] == site
    with (ROOT / "exports/readings/lp2-56.csv").open(encoding="utf-8", newline="") as f:
        reading = [int(row["output_index"]) for row in csv.DictReader(f)]
    assert len(reading) == 85
    return list(zip(ids,pages[:55])) + [("joined",[x for page in pages[:55] for x in page])], reading


def controls(matrix_groups, reading):
    scorer = score_module.default()
    result = {}
    for group, matrix in matrix_groups.items():
        for op, transform in variants(matrix).items():
            n = len(transform)
            padding = (-len(reading)) % n
            plain = reading + [0] * padding
            inv = inverse(transform)
            assert inv is not None
            cipher = apply(plain, inv)
            recovered = apply(cipher, transform)
            assert recovered == plain and recovered[:len(reading)] == reading
            assert recovered[len(reading):] == [0] * padding
            measured = scorer.score_norm(gp.indices_to_translit(recovered[:len(reading)]))
            assert measured > -5.0
            result[group + "." + op] = {"recovered_runes": len(reading),
                                          "zero_padding_removed": padding,
                                          "score": round(measured, 6)}
    return result


def block_coverage(targets):
    result={}
    for n in (4,5):
        pages=[indices for name,indices in targets if name!='joined']
        joined=targets[-1][1]
        result[str(n)]={"page_runes":sum(map(len,pages)),
                        "page_tail_runes_dropped":sum(len(p)%n for p in pages),
                        "pages_with_tail":sum(bool(len(p)%n) for p in pages),
                        "joined_runes":len(joined),
                        "joined_tail_runes_dropped":len(joined)%n}
    return result


def score_cases(targets, matrix_groups):
    scorer = score_module.default()
    rows = []
    for group, raw in matrix_groups.items():
        for op, matrix in variants(raw).items():
            for target, indices in targets:
                text = gp.indices_to_translit(apply(indices, matrix))
                rows.append({"group":group,"op":op,"target":target,
                             "score":round(scorer.score_norm(text), 9),
                             "preview":text[:70]})
    return rows


def compute_null(targets, matrix_groups, trials=199):
    """Shuffle each page once/trial, then share that corpus across all arms."""
    rng = random.Random(3301)
    original = [x for name,x in targets if name != "joined"]
    source_names = [name for name,_ in targets if name != "joined"]
    maxima = []
    for _ in range(trials):
        shuffled = [page[:] for page in original]
        for page in shuffled:
            rng.shuffle(page)
        t = list(zip(source_names,shuffled)) + [("joined",[x for page in shuffled for x in page])]
        rows = score_cases(t,matrix_groups)
        maxima.append({"source_max":max(x["score"] for x in rows if x["group"]!="M3_image_cell"),
                       "corrected_max":max(x["score"] for x in rows if x["group"]=="M3_image_cell")})
    return maxima


def compute():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    assert sha(SCRIPT) == plan["source_sha256"]
    assert sha(SRC / "data/krisyotam_runes.txt") == plan["input_hashes"]["source_rune_text_sha256"]
    assert sha(SRC / "data/english_quadgrams.txt") == plan["input_hashes"]["source_quadgrams_sha256"]
    assert sha(ROOT / "data/pages/lp2-15.json") == plan["input_hashes"]["site_lp2_15_json_sha256"]
    source_receipt = source_replay()
    targets, reading = pages_and_reading()
    matrices = source_matrices()
    printed = json.loads((ROOT / "data/pages/lp2-15.json").read_text(encoding="utf-8"))["numbers"]
    assert matrices["M3_4x4"][:-1] == printed[:-1]
    assert matrices["M3_4x4"][-1][:-1] == printed[-1][:-1]
    assert matrices["M3_4x4"][-1][-1] == 820 and printed[-1][-1] == 1820
    corrected = [row[:] for row in matrices["M3_4x4"]]
    corrected[-1][-1] = 1820
    groups = dict(matrices, M3_image_cell=corrected)
    planted = controls(groups,reading)
    cases = score_cases(targets,groups)
    source_cases = [x for x in cases if x["group"]!="M3_image_cell"]
    source_best = max(source_cases,key=lambda x:x["score"])
    archived = json.loads(ARCHIVED.read_text(encoding="utf-8"))
    assert round(source_best["score"],3) == archived["best_score"]
    assert (source_best["group"],source_best["op"]) == (archived["best"]["matrix"],archived["best"]["variant"])
    # Source p54 is the 55th rune-bearing segment, after runeless LP2-50.
    assert source_best["target"] == "lp2-55"
    assert source_best["preview"] == archived["best"]["text"]
    for pair, saved in archived["per_matrix_best"].items():
        group, operation = pair.split(".")
        assert round(max(x["score"] for x in source_cases if x["group"]==group and x["op"]==operation),3) == saved
    null = compute_null(targets,groups)
    corrected_cases = [x for x in cases if x["group"]=="M3_image_cell"]
    corrected_best = max(corrected_cases,key=lambda x:x["score"])
    result = {"schema":"liberpedia-book-matrix-hill-results-v1", "plan_sha256":sha(HERE/"plan.json"),
              "source_replay":source_receipt,"page_parity":"55 of 55 site/source rune arrays identical",
              "matrix_cell":{"source":820,"image_transcription":1820,"row":4,"column":4},
              "block_coverage":block_coverage(targets),
              "source_arms":24,"corrected_arms":4,"targets":56,"case_count":len(cases),
              "planted_controls":planted,"source_best":source_best,"corrected_best":corrected_best,
              "source_over_bar":sum(x["score"]>-5 for x in source_cases),
              "corrected_over_bar":sum(x["score"]>-5 for x in corrected_cases),
              "conditional_null":{"seed":3301,"trials":199,"rows":null,
                                  "source_max_ge_observed":sum(x["source_max"]>=source_best["score"] for x in null),
                                  "corrected_max_ge_observed":sum(x["corrected_max"]>=corrected_best["score"] for x in null)},
              "cases":cases}
    return result


def write_json(path, data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    result=compute()
    if args.check:
        assert json.loads(OUT.read_text(encoding="utf-8"))==result
        print("PASS source replay, corrected input, 1,568 cases, 199 whole-grid nulls")
    else:
        write_json(OUT,result)
        print("source best",result["source_best"]["score"],"corrected",result["corrected_best"]["score"])
