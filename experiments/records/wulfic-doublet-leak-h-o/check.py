"""Independent H/O pair extraction and all-row arithmetic from site text and saved source controls."""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
N = 29


def near(a: float, b: float, label: str, tol: float = 1e-8) -> None:
    assert math.isclose(a, b, rel_tol=tol, abs_tol=tol), f"{label}: {a} != {b}"


def poisson_upper(k: int, mean: float) -> float:
    if mean == 0:
        return 0.
    term = math.exp(-mean + k*math.log(mean) - math.lgamma(k+1))
    total = 0.
    for j in range(k, k+1000):
        total += term
        term *= mean/(j+1)
        if term < total*1e-17:
            break
    return total


def binom_upper(k: int, n: int, p: float) -> float:
    return sum(math.exp(math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)
                        +i*math.log(p)+(n-i)*math.log1p(-p)) for i in range(k,n+1))


def primes(count: int) -> list[int]:
    vals, x = [], 2
    while len(vals) < count:
        if all(x%d for d in range(2, math.isqrt(x)+1)):
            vals.append(x)
        x += 1
    return vals


def main() -> None:
    inp = json.loads((HERE/"inputs.json").read_text(encoding="utf-8"))
    res = json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    lookup = {r:i for i,r in enumerate(RUNES)}
    assert len(lookup) == N
    stream, lines, page_ids = [], [], []
    global_line = 0
    for n in range(56):
        page = json.loads((ROOT/"data"/"pages"/f"lp2-{n:02}.json").read_text(encoding="utf-8"))
        for ch in page["raw"]:
            if ch == "/":
                global_line += 1
            elif ch in lookup:
                stream.append(lookup[ch]); lines.append(global_line); page_ids.append(n)
    assert len(stream) == 12956
    lengths = inp["source_segment_lengths"]
    assert lengths == [729,1145,1729,9,1894,1021,1524,1589,3316]
    rows, start = [], 0
    for seg, size in enumerate(lengths, 7):
        for i in range(size-1):
            j = start+i
            rows.append([seg,i,j,stream[j],stream[j+1],int(lines[j]!=lines[j+1]),
                         int(page_ids[j]!=page_ids[j+1])])
        start += size
    assert rows == inp["pairs"], "source pairs/layout differ from independently parsed site pages"
    assert len(rows) == res["pairs"] == 12947
    hits = [r for r in rows if r[3] == r[4]]
    assert len(hits) == res["doublets"] == 86
    hist = Counter((r[4]-r[3])%N for r in rows)
    counts = [hist[i] for i in range(N)]
    assert counts == res["H_L1"]["difference_counts"]
    mean = (len(rows)-counts[0])/(N-1)
    for i in range(1,N):
        near((counts[i]-mean)/math.sqrt(mean),res["H_L1"]["z"][i],"L1 z")
    grouping = {"within-line":[0,0],"line-break":[0,0],"page-break":[0,0]}
    for r in rows:
        hit = int(r[3]==r[4])
        key = "line-break" if r[5] else "within-line"
        grouping[key][0] += hit; grouping[key][1] += 1
        if r[6]:
            grouping["page-break"][0] += hit; grouping["page-break"][1] += 1
    assert grouping == res["H_L2"]["break_counts"]
    for row in res["H_L3"]["periods"]:
        m = row["period"]
        clock = 2 if row["clock"] == "joined" else 1
        slots = [0]*m; events = [0]*m
        for r in rows:
            j = r[clock]%m
            slots[j] += 1; events[j] += (r[3]==r[4])
        top = max(events)
        p = min(1.,sum(binom_upper(top,len(hits),size/len(rows)) for size in slots))
        assert top == row["top"]
        near(p,row["p"],"L3 phase tail",1e-7)
    by_seg = {seg:[0,0] for seg in range(7,16)}
    for r in rows:
        by_seg[r[0]][0] += int(r[3]==r[4]); by_seg[r[0]][1] += 1
    rate = len(hits)/len(rows)
    chi = sum((obs-n*rate)**2/(n*rate) + ((n-obs)-n*(1-rate))**2/(n*(1-rate))
              for obs,n in by_seg.values())
    near(chi,res["H_L4"]["chi2"],"L4 chi2")
    assert res["H_L4"]["df"] == 8
    h = chi/2
    p = math.exp(-h)*sum(h**i/math.factorial(i) for i in range(4))
    near(p,res["H_L4"]["p"],"L4 chi2 tail")
    win = [sum(r[3]==r[4] for r in rows[i:i+500]) for i in range(0,len(rows)-499,500)]
    avg = sum(win)/len(win)
    disperse = sum((x-avg)**2 for x in win)/(len(win)-1)/avg
    near(disperse,res["H_L4"]["dispersion_500"],"L4 dispersion")
    plain = inp["solved_plain"]
    assert len(plain) == 2901
    prime = primes(len(plain))
    keys = {
        "DIVINITY/CIRCUMFERENCES": ([inp["divinity_key"][i%8] for i in range(len(plain))],
                                    [inp["circumferences_key"][i%14] for i in range(len(plain))]),
        "phi(prime)/primes": ([(v-1)%N for v in prime],[v%N for v in prime])
    }
    for row in res["H_L5"]["key_switches"]:
        first, second = keys[row["keys"]]
        if row["kind"] == "ideal":
            cipher = []
            for i,p in enumerate(plain):
                value = (p+first[i])%N
                if cipher and value == cipher[-1]:
                    value = (p+second[i])%N
                cipher.append(value)
        else:
            cipher = []
            for i,p in enumerate(plain):
                if i+1<len(plain) and (plain[i+1]+first[i+1])%N == (p+first[i])%N:
                    value = None if (plain[i+1]+second[i+1])%N == (p+second[i])%N else (p+second[i])%N
                else:
                    value = (p+first[i])%N
                cipher.append(value)
        eligible = [(a,b) for a,b in zip(cipher,cipher[1:]) if a is not None and b is not None]
        observed = sum(a==b for a,b in eligible)
        assert (observed,len(eligible)) == (row["hits"],row["pairs"])
        near(poisson_upper(86,observed/len(eligible)*len(rows)),row["lp2_upper_tail"],"L5 Poisson")
    dp_counts = Counter((b-a)%N for a,b in zip(plain,plain[1:]))
    dp = [dp_counts[i]/(len(plain)-1) for i in range(N)]
    for a,b in zip(dp,res["O_C14"]["solved_plain_difference_model"]):
        near(a,b,"C14 plaintext differences")
    repeat = res["O_C14"]["repeat_rate"]
    model = [repeat*dp[e]+(1-repeat)/(N-1)*(1-dp[e]) for e in range(1,N)]
    norm = sum(model)
    llr = sum(counts[e]*math.log((model[e-1]/norm)*(N-1)) for e in range(1,N))
    near(llr,res["O_C14"]["lp2_llr"],"C14 LLR")
    assert llr <= -10
    print("H/O: 12,947 pairs and all source manuscript statistics independently checked")


if __name__ == "__main__":
    main()
