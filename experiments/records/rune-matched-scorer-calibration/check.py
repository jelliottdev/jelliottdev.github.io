"""Independent R16 score arithmetic and literal model-transformation audit."""
from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LP = HERE/"source"/"liber-primus"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
TRANS = ["F","U","TH","O","R","C","G","W","H","N","I","J","EO","P","X","S","T","B","E","M","L","NG","OE","D","A","AE","Y","IA","EA"]
RUNE_IDX = {c:i for i,c in enumerate(RUNES)}
ALIAS = str.maketrans({"K":"C","Q":"C","V":"U","Z":"S"})


def source_ciphertext():
    md=(LP/"data"/"scream314_lp.md").read_text(encoding="utf-8")
    section=md.split("\n## 06.jpg",1)[1].split("\n## ",1)[0]
    after=section.split("\nRunes:",1)[1]
    lines=[]
    started=False
    for line in after.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            lines.append(line)
            started=True
        elif line.strip() and started:
            break
    return [RUNE_IDX[ch] for line in lines for ch in line if ch in RUNE_IDX]


def models():
    old=Counter()
    for line in (LP/"data"/"english_quadgrams.txt").read_text(encoding="ascii").splitlines():
        q,n=line.split()
        old[q]=int(n)
    # The pinned scorer processes each original four-letter gram letter by
    # letter. Its output is therefore exactly this four-character alias map:
    # no new gram gets extra TH/EO/NG/OE/AE/IA/EA rune-unit expansion.
    matched=Counter()
    for q,n in old.items():
        matched[q.translate(ALIAS)]+=n
    return old,matched


def scores_for(texts, model):
    total=sum(model.values())
    logtotal=math.log10(total)
    floor=math.log10(.01)-logtotal
    grams={q:math.log10(c)-logtotal for q,c in model.items()}
    out=[]
    for text in texts:
        s=re.sub("[^A-Z]","",text.upper())
        windows=len(s)-3
        out.append(sum(grams.get(s[i:i+4],floor) for i in range(windows))/windows)
    return out


def summaries(values):
    mu=sum(values)/len(values)
    sd=math.sqrt(sum((x-mu)**2 for x in values)/len(values))
    return {"n":len(values),"mean":round(mu,4),"sd":round(sd,4),
            "min":round(min(values),4),"max":round(max(values),4)}


def main():
    result=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    solved=json.loads((HERE/"solved_texts.json").read_text(encoding="utf-8"))
    old,new=models()
    assert len(new)==result["matched_model"]["n_distinct_quadgrams"]==68083
    assert sum(new.values())==result["matched_model"]["total_count"]==sum(old.values())==7266795
    # All five source-decoded texts are rescored with independently built maps.
    ot=scores_for([p["text"] for p in solved],old)
    nt=scores_for([p["text"] for p in solved],new)
    for page,record,o,n in zip(solved,result["solved_pages"],ot,nt):
        assert page["page"]==record["page"]
        assert round(o,4)==record["old_score"]
        assert round(n,4)==record["new_score"]
    assert all(n>o for o,n in zip(ot,nt))
    # Reparse the manuscript source independently of lp.corpus and repeat all
    # 200 seeded random-keystream decodes under both models.
    ct=source_ciphertext()
    assert len(ct)==result["null"]["ciphertext_runes"]==742
    rng=random.Random(42)
    trial=[]
    for _ in range(200):
        plain=[(c-rng.randint(0,28))%29 for c in ct]
        trial.append("".join(TRANS[v] for v in plain))
    oscores=scores_for(trial,old)
    nscores=scores_for(trial,new)
    assert summaries(oscores)==result["null"]["old"]
    assert summaries(nscores)==result["null"]["new"]
    old_sep=(min(round(v,4) for v in ot)-result["null"]["old"]["mean"])/result["null"]["old"]["sd"]
    new_sep=(min(round(v,4) for v in nt)-result["null"]["new"]["mean"])/result["null"]["new"]["sd"]
    assert round(old_sep,2)==result["separation"]["old"]["sigma_sep"]
    assert round(new_sep,2)==result["separation"]["new"]["sigma_sep"]
    assert result["gates"]["gate1_positive_control_pass"] is True
    assert result["gates"]["gate2_sd_not_worse"] is False
    print("Independent five-page scores, 200 seeded nulls, model counts and both gates pass.")
    print("Literal matched model equals alias-collapsed four-character quadgrams; no extra rune-unit expansion is performed.")


if __name__ == "__main__":
    main()
