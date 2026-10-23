"""Bound lag-six and doublet counts under two page-break tokenization rules."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
LAG=6

def words(source: str, rune_map: dict[str,int]) -> list[list[int]]:
    result=[]
    for piece in re.split(r'[-.]',source):
        token=[rune_map[c] for c in piece if c in rune_map]
        if token: result.append(token)
    return result

def stats(tokens: list[list[int]]) -> dict:
    return {"tokens":len(tokens), "runes":sum(map(len,tokens)),
            "lag_six_opportunities":sum(max(0,len(w)-LAG) for w in tokens),
            "lag_six_matches":sum(b == (24-2*a)%29 for w in tokens for a,b in zip(w,w[LAG:])),
            "adjacent_opportunities":sum(len(w)-1 for w in tokens),
            "adjacent_doublets":sum(a==b for w in tokens for a,b in zip(w,w[1:])),
            "maximum_word_runes":max(map(len,tokens))}

def report() -> dict:
    alphabet_blob=(ROOT/'data/index.json').read_bytes()
    alphabet=json.loads(alphabet_blob)['alphabet']
    rune_map={r['rune']:i for i,r in enumerate(alphabet)}
    assert len(rune_map)==29
    inputs={"data/index.json":hashlib.sha256(alphabet_blob).hexdigest()}
    pages=[]
    for i in range(56):
        path=f'text/lp2-{i:02}.txt'
        blob=(ROOT/path).read_bytes()
        inputs[path]=hashlib.sha256(blob).hexdigest()
        page=blob.decode('utf8')
        assert not ({c for c in page if '\u16a0'<=c<='\u16ff'}-rune_map.keys())
        pages.append(page)
    separate=[w for page in pages for w in words(page,rune_map)]
    joined=words(''.join(pages),rune_map)
    edge_rows=[]
    for i in range(55):
        left=pages[i].replace('/','').strip()
        right=pages[i+1].replace('/','').strip()
        candidate=left[-1:] in rune_map and right[:1] in rune_map
        left_word=words(left,rune_map)[-1] if candidate else []
        right_word=words(right,rune_map)[0] if candidate else []
        pair_cross_count=0
        pair_cross_matches=0
        if candidate:
            combined=left_word+right_word
            for p in range(max(0,len(left_word)-LAG),len(left_word)):
                if p+LAG>=len(combined):continue
                pair_cross_count+=1
                pair_cross_matches+=combined[p+LAG] == (24-2*combined[p])%29
        edge_rows.append({"left":f'lp2-{i:02}',"right":f'lp2-{i+1:02}',
                          "rune_to_rune":candidate,"left_edge":left[-1:],"right_edge":right[:1],
                          "added_lag_six_pairs_if_joined":pair_cross_count,
                          "added_lag_six_matches_if_joined":pair_cross_matches,
                          "added_adjacent_doublet_if_joined":int(candidate and left_word[-1]==right_word[0])})
    a,b=stats(separate),stats(joined)
    assert a['runes']==b['runes']==12956
    assert sum(e['rune_to_rune'] for e in edge_rows)==32
    for key in ('lag_six_opportunities','lag_six_matches','adjacent_doublets'):
        suffix={'lag_six_opportunities':'added_lag_six_pairs_if_joined',
                'lag_six_matches':'added_lag_six_matches_if_joined',
                'adjacent_doublets':'added_adjacent_doublet_if_joined'}[key]
        assert b[key]-a[key]==sum(e[suffix] for e in edge_rows)
    return {"input_sha256":inputs,"rule":"The published word-internal-affine-lags delimiter rule; page split versus page join only.",
            "split_pages":a,"joined_pages":b,"difference":{k:b[k]-a[k] for k in a if k!='maximum_word_runes'},
            "candidate_page_joins":32,"boundary_details":edge_rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    payload=json.dumps(report(),ensure_ascii=False,indent=2)+'\n'
    out=HERE/'results.json'
    if args.check:assert out.read_text(encoding='utf8')==payload
    else:out.write_text(payload,encoding='utf8')
    r=json.loads(payload)
    print(r['split_pages'],r['joined_pages'])

if __name__=='__main__':main()
