#!/usr/bin/env python3
"""Independent arithmetic and provenance checks for the source replay."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = {ch: i for i, ch in enumerate("ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ")}
LATIN = ["F","U","TH","O","R","C","G","W","H","N","I","J","EO","P","X","S","T","B","E","M","L","NG","OE","D","A","AE","Y","IO","EA"]


def ast_assignment(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(name)


def source_bytes(source_file, repo):
    if source_file:
        return Path(source_file).read_bytes()
    if repo:
        return subprocess.check_output(["git", "show", "HEAD:tools/legacy/transposition_solver.py"], cwd=repo)
    raise ValueError("pass --source-file or --source-repo for exact source audit")


def keyword_values(keyword):
    token = {name: i for i, name in enumerate(LATIN)}
    result = []
    i = 0
    while i < len(keyword):
        found = next((keyword[i:i+n] for n in (3, 2)
                      if keyword[i:i+n] in token), None)
        if found:
            result.append(token[found])
            i += len(found)
        else:
            result.append(token.get({'K': 'C', 'V': 'U'}.get(keyword[i], keyword[i]), 0))
            i += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file")
    parser.add_argument("--source-repo")
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    inputs = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    raw_source = source_bytes(args.source_file, args.source_repo)
    assert hashlib.sha256(raw_source).hexdigest() == plan["source_sha256"] == result["source_sha256"]
    tree = ast.parse(raw_source)
    keys = ast_assignment(tree, "PAGE_KEYS")
    bigrams = ast_assignment(tree, "ENGLISH_BIGRAMS")
    assert len(result["pages"]) == len(inputs["pages"]) == 10
    assert len(result["controls"]) == 80 and all(row["pass"] for row in result["controls"])
    assert result["wordset_size"] == 95
    for row in result["pages"]:
        pg = row["source_page"]
        page_id = row["current_page"]
        assert page_id == f"lp2-{pg-17:02d}"
        f = ROOT / "data" / "pages" / f"{page_id}.json"
        assert hashlib.sha256(f.read_bytes()).hexdigest() == inputs["pages"][page_id]["canonical_sha256"]
        source_input = inputs["pages"][page_id]
        assert source_input["exact_rune_match"] and source_input["runes"] == row["runes"]
        if args.source_repo:
            b = subprocess.check_output(["git", "show", "HEAD:" + source_input["source_path"]], cwd=args.source_repo)
            assert hashlib.sha256(b).hexdigest() == source_input["source_sha256"]
            assert [RUNES[ch] for ch in b.decode("utf-8") if ch in RUNES] == [RUNES[ch] for ch in json.loads(f.read_text(encoding="utf-8"))["raw"] if ch in RUNES]
        raw = json.loads(f.read_text(encoding="utf-8"))["raw"]
        cipher = [RUNES[ch] for ch in raw if ch in RUNES]
        key = keys[pg]["indices"]
        if key is None:
            key = keyword_values(keys[pg]["keyword"])
        mode = keys[pg]["mode"]
        decoded = []
        for i, c in enumerate(cipher):
            k = key[i % len(key)]
            decoded.append({"sub": lambda: (c-k)%29,
                            "add": lambda: (c+k)%29,
                            "beaufort": lambda: (k-c)%29}[mode]())
        text = "".join(LATIN[x] for x in decoded)
        baseline = sum(bigrams.get(text[i:i+2], -1) for i in range(len(text)-1)) - 2
        assert baseline == row["baseline_score"]
    for row in result["pages"]:
        assert row["best"]["score"] == max(x["score"] for x in row["rows"])
        assert sum(x["method"] == "NO_TRANSPOSITION" for x in row["rows"]) == 1
        assert all(x["matched"] == 0 for x in row["rows"])
        assert row["source_row_count"] == len(row["rows"])
    assert sum(len(row["rows"]) for row in result["pages"]) == 585
    print("independent baseline, source-input, selection and zero-word checks passed")


if __name__ == "__main__":
    main()
