"""Independent scalar reconstruction of every direction-grid result and null."""
from __future__ import annotations

import hashlib
import json
import math
import random
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "source"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LATIN = ("F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO",
         "P", "X", "S", "T", "B", "E", "M", "L", "NG", "OE", "D", "A", "AE",
         "Y", "IA", "EA")
MAP = {r:i for i,r in enumerate(RUNES)}
KEY = (23, 10, 1, 10, 9, 10, 16, 26)  # DIVINITY, with V=U


def load():
    raw = (SRC / "data/krisyotam_runes.txt").read_text(encoding="utf8")
    pages = []
    for segment in raw.split("%"):
        lines = [[MAP[c] for c in line if c in MAP] for line in segment.split("/")]
        lines = [line for line in lines if line]
        if lines:
            pages.append(lines)
    assert len(pages) == 57
    table = {}
    total = 0
    for line in (SRC / "data/english_quadgrams.txt").read_text(encoding="ascii").splitlines():
        word, value = line.split()
        table[word] = int(value)
        total += int(value)
    return pages, {k: math.log10(v)-math.log10(total) for k,v in table.items()}, math.log10(.01)-math.log10(total)


def routes(lines):
    flat = [v for row in lines for v in row]
    yield "rows", flat
    yield "reversed", flat[::-1]
    yield "boustro", [v for i,row in enumerate(lines) for v in (row if i%2==0 else row[::-1])]
    col = [row[x] for x in range(max(map(len, lines))) for row in lines if x < len(row)]
    yield "colmajor", col
    yield "colmajor_rev", col[::-1]


@lru_cache(None)
def primes(count):
    out = []
    x = 2
    while len(out) < count:
        if all(x % p for p in out if p*p <= x):
            out.append(x)
        x += 1
    return tuple(out)


def phi(n):
    result = n
    factor = 2
    while factor*factor <= n:
        if n % factor == 0:
            while n % factor == 0:
                n //= factor
            result -= result // factor
        factor += 1
    if n > 1:
        result -= result // n
    return result


@lru_cache(None)
def keys(n):
    pp = primes(n)
    return (tuple(p%29 for p in pp), tuple((p-1)%29 for p in pp),
            tuple(phi(i+2)%29 for i in range(n)))


def candidates(cipher):
    n = len(cipher)
    yield "direct", cipher
    yield "atbash", [28-c for c in cipher]
    for shift in range(1,29):
        yield f"shift{shift}", [(c-shift)%29 for c in cipher]
    for label, stream in zip(("prime", "prime-1", "totient"), keys(n)):
        for sign in (-1,1):
            yield f"{label}{sign:+d}", [(c+sign*stream[i])%29 for i,c in enumerate(cipher)]
    yield "DIVINITY", [(c-KEY[i%len(KEY)])%29 for i,c in enumerate(cipher)]


def score(plain, model, floor):
    text = "".join(LATIN[c] for c in plain)
    return sum(model.get(text[i:i+4], floor) for i in range(len(text)-3))/(len(text)-3)


def grid(pages, model, floor):
    best = (-999.0, None)
    orderbest = {}
    pagebest = []
    digest = hashlib.sha256()
    count = 0
    for page_index, lines in enumerate(pages):
        local = (-999.0,None)
        for name, route in routes(lines):
            for mode, plain in candidates(route):
                value = score(plain, model, floor)
                count += 1
                digest.update(f"{page_index}|{name}|{mode}|{value:.12f}|".encode())
                digest.update(bytes(plain))
                rec = {"source_page":page_index,"order":name,"cipher":mode,"score":value}
                if value > best[0]: best = (value,rec)
                if value > local[0]: local = (value,rec)
                orderbest[name] = max(orderbest.get(name,-999),value)
        pagebest.append(local[1])
    return {"best":best[1],"per_order_best":orderbest,
            "candidate_count":count,"grid_sha256":digest.hexdigest(),"page_best":pagebest}


def shuffle_pages(pages, rng):
    out=[]
    for lines in pages:
        flat=[v for line in lines for v in line]
        rng.shuffle(flat)
        lengths=list(map(len,lines))
        start=0
        nextlines=[]
        for length in lengths:
            nextlines.append(flat[start:start+length]);start+=length
        out.append(nextlines)
    return out


def check_site_mapping(pages):
    root = HERE.parents[2]
    for source_number, lines in enumerate(pages):
        site_number = source_number if source_number < 50 else source_number + 1
        page = json.loads((root / f"data/pages/lp2-{site_number:02d}.json").read_text(encoding="utf8"))
        site_runes = [MAP[ch] for line in page["lines"] for ch in line["raw"] if ch in MAP]
        source_runes = [v for line in lines for v in line]
        assert site_runes == source_runes, (source_number, site_number)


def compare(observed, saved):
    assert observed["candidate_count"] == saved["candidate_count"]
    # The producer hashes decimal renderings of binary floating-point scores.
    # This independent scorer uses a distinct summation path; compare values
    # numerically rather than assuming identical final binary rounding.
    for k in ("source_page","order","cipher"):
        assert observed["best"][k] == saved["best"][k]
    assert abs(observed["best"]["score"]-saved["best"]["score"]) < 1e-10
    for order,value in observed["per_order_best"].items():
        assert abs(value-saved["per_order_best"][order]) < 1e-10


if __name__ == "__main__":
    saved=json.loads((HERE/"results.json").read_text(encoding="utf8"))
    pages, model, floor=load()
    check_site_mapping(pages)
    print("PASS all 57 source-to-site page sequences",flush=True)
    real=grid(pages[:55],model,floor)
    compare(real,saved["real"])
    for a,b in zip(real["page_best"],saved["real"]["page_best"]):
        assert (a["source_page"],a["order"],a["cipher"]) == (b["source_page"],b["order"],b["cipher"])
        assert abs(a["score"]-b["score"]) < 1e-10
    print("PASS independent complete real grid",flush=True)
    rng=random.Random(3301)
    scores=[]
    for i, expected in enumerate(saved["null_controls"]):
        result=grid(shuffle_pages(pages[:55],rng),model,floor)
        assert result["candidate_count"] == expected["candidate_count"]
        for key in ("source_page","order","cipher"):
            assert result["best"][key] == expected["best_"+key]
        assert abs(result["best"]["score"]-expected["best_score"]) < 1e-10
        scores.append(result["best"]["score"])
        print(f"PASS independent null {i+1}/{len(saved['null_controls'])}",flush=True)
    assert sum(v >= real["best"]["score"] for v in scores) == saved["null_at_least_observed"]
    print("PASS every saved control and selection count")
