"""Recount T2 control receipts independently of the image/source algorithms."""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE.parent / "dukotah-t2-fresh-template-loo"


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group(seg):
    return "solved-LP2" if seg >= 55 else "dense-45-54" if seg >= 45 else "pages-0-44"


def main():
    plan, result = read("plan.json"), read("results.json")
    assert sha(HERE / "plan.json") == result["plan_sha256"]
    assert sha(BASE / "plan.json") == plan["input_plan_sha256"]
    assert sha(BASE / "templates.npz") == plan["fresh_template_npz_sha256"]
    assert sha(BASE / "diff_report.json") == plan["fresh_mapping_sha256"]
    for name, digest in result["file_sha256"].items():
        assert sha(HERE / name) == digest, name
    lm = read("out_linemap.json")["map"]
    probe = read("out_probe_fresh.json")
    assert len(lm) == len(probe) == 604
    assert [r["gline"] for r in lm] == [r["gline"] for r in probe] == list(range(604))
    for r in lm:
        seg = r["seg"]
        assert r["num"] == (seg if seg <= 49 else seg + 1 if seg <= 54 else seg + 18)
    assert sum(len(r["best"]) for r in probe) == 13121
    assert sum(sum(a == b for a, b in zip(r["canon"], r["best"])) for r in probe if r["seg"] >= 55) == 178

    sp = read("out_splice.json")
    agg = collections.defaultdict(lambda: {"n": 0, "det": 0, "rec": 0})
    for x in sp["results"]:
        assert x["spliced"] != x["canon"]
        assert x["detect"] == int(x["probe"] != x["canon"])
        assert x["recover"] == int(x["probe"] == x["spliced"])
        a = agg[x["stratum"]]
        a["n"] += 1
        a["det"] += x["detect"]
        a["rec"] += x["recover"]
    assert dict(agg) == sp["agg"] == result["splice_by_source_stratum"]
    assert len(sp["results"]) == 545 and sp["n_per_stratum"] == 200
    assert sp["excluded_pairs"] == 4774 and sp["total_pairs"] == 16184
    assert agg["dense-45-54"]["rec"] / agg["dense-45-54"]["n"] >= .5

    ind = read("out_indel.json")
    score = read("out_indel_score.json")
    adj = read("out_indel_adj.json")
    assert len(ind["rows"]) == 604 and len(ind["plants"]) == 1208
    assert sum(r["L"] for r in ind["rows"]) == score["n_positions"] == 13121
    pooled = collections.defaultdict(lambda: {"n": 0, "fired": 0, "loc": 0})
    strata = collections.defaultdict(lambda: {"n": 0, "fired": 0, "loc": 0, "rune": 0, "nr": 0})
    for p in ind["plants"]:
        for a in (pooled[p["kind"]], strata[p["kind"] + "|" + p["stratum"]]):
            a["n"] += 1
            a["fired"] += p["fired"]
            a["loc"] += p["loc"]
        if p["rune"] is not None:
            a = strata[p["kind"] + "|" + p["stratum"]]
            a["nr"] += 1
            a["rune"] += p["rune"]
    assert dict(pooled) == score["pooled"] == result["indel_pooled"]
    assert dict(strata) == score["per_stratum"]
    solved = [r for r in ind["rows"] if r["stratum"] == "solved-LP2"]
    assert len(solved) == 10
    tau_del = max(0.0, max(r["max_del"] for r in solved))
    tau_ins = max(0.0, max(r["max_ins"] for r in solved))
    assert (tau_del, tau_ins) == (score["tau_del"], score["tau_ins"]) == (0.0, 0.0)
    flags = [(kind, r["gline"]) for r in ind["rows"] for kind, val, tau in
             (("DEL", r["max_del"], tau_del), ("INS", r["max_ins"], tau_ins)) if val > tau]
    assert sorted(flags) == sorted((kind, r["gline"]) for kind, r in score["flags"])
    assert sorted(flags) == sorted((r["kind"], r["gline"]) for r in adj)
    assert len(flags) == 26 and all(r["verdict"] == "SEG" for r in adj)
    assert collections.Counter(group(lm[g]["seg"]) for _, g in flags) == collections.Counter({"pages-0-44": 24, "dense-45-54": 2})

    sep = read("out_separators.json")
    srows = sep["rows"]
    assert len(srows) == 604
    sums = {k: sum(r[k] for r in srows) for k in ("canon_dash", "canon_dot", "img_dash", "img_dot")}
    sums.update(lines=604,
                count_exact=sum((r["canon_dash"], r["canon_dot"]) == (r["img_dash"], r["img_dot"]) for r in srows),
                pos_exact=sum(not r["dis"] for r in srows))
    assert sums == sep["totals"] == result["separator_totals"]
    assert sum(not r["dis"] for r in srows if r["seg"] >= 55) == 10
    shortlist = read("out_sep19.json")
    assert len(shortlist) == 19 and len({r["gline"] for r in shortlist}) == 19
    byline = {r["gline"]: r for r in srows}
    for r in shortlist:
        s = byline[r["gline"]]
        assert (r["canon_dash"], r["canon_dot"], r["img_dash"], r["img_dot"]) == (
            s["canon_dash"], s["canon_dot"], s["img_dash"], s["img_dot"])
        assert r["klass"] == "alignment"  # script's rule, not independent visual adjudication
        assert (s["canon_dash"], s["canon_dot"]) == (s["img_dash"], s["img_dot"])
    assert result["unrun_registered_control"] == "C4 deleted-separator plant (8/10 gate)"
    print("T2 controls checked: 545/545 splice recoveries, 1,208 indel plants, 26 flagged lines, 19 count-equal shortlist rows")


if __name__ == "__main__":
    main()
