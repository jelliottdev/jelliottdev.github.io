"""Declare a draft Liberpedia record with exact artifact hashes."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ID=HERE.name
BASE=f'experiments/records/{ID}/'
def hashed(relative): return {'path':relative,'sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()}
def main():
    rec={
      'id':ID,'status':'draft',
      'title':'Does the fractionation reversal undo its own shuffle?',
      'question':'What do the archived 6×5 keyword-grid routes produce on six intended LP2 pages, and does the archived columnar reversal invert its forward transform?',
      'reader_question':'Does this grid-and-shuffle method work on LP2?',
      'summary':'The archived reversal fails 476 of 588 planted round trips. A repaired inverse passes all 588, but neither route yields a verified page reading under the source’s limited keyword and width grid.',
      'finding':'The source names 1,260 settings; its own length rule skips 336, and 2 of the remaining 924 cross its vocabulary-score gate. Its raw IoC is bounded by 1, so the IoC >1.3 gate cannot fire. A separately labeled exact inverse produces 2 score-gated rows among 588 settings. Every gated setting has invalid grid cells. The correction repairs a transposition inverse; it does not identify the manuscript cipher.',
      'limitations':'Only 14 source keywords, six checked page streams, five split rules, seven natural-order column widths and two coordinate shifts. The source gate can reward a few words even when invalid cells were dropped; raw IoC is not normalized or controlled. No general fractionation or plaintext verdict.',
      'next_steps':'Specify a coordinate-stream encoding, a single keyed transposition, null treatment and a held-out reading before interpreting further keyword matches.',
      'outcome':'inconclusive',
      'tags':['LP2','source-derived test','fractionation','Polybius grid','columnar transposition','source audit'],
      'scope':{
        'pages':['lp2-21','lp2-22','lp2-23','lp2-27','lp2-28','lp2-30'],
        'artifacts':[BASE+'plan.json'],
        'representation':'Source GP29 rune order; 6×5 keyword-first table with the last cell empty. Archived source page_38/39/40/44/45/47 rune streams independently match the corresponding current LP2 pages under the source parser.',
        'procedure':'Replay split, archived column reversal, direct and coordinate-shift routes exactly. Separately correct natural-order column lengths and compare 588 full-message planted round trips.',
        'parameters':'14 source keywords; six source-intended LP2 pages; split n/n−5/n+5/n//2/2n//3; widths 7,11,13,17,19,23,29; sub/add coordinate shifts.',
        'exclusions':'Other widths, keys, keyed column orders, coordinate-stream encodings, alternate null handling, source bonus running-key methods and any decryption claim.'},
      'review':{'kind':'source-defined bounded replay plus separately identified inverse repair','retested_on':'2026-10-23','reviewer':'All 1,512 scored routes checked against AST-extracted pinned source functions; 588 planted controls and exact page parser alignments','human_review':'pending'},
      'reproduction':{
        'command':f'python {BASE}run.py --check',
        'environment':'Python 3 standard library; optional pinned Wulfic Git checkout for source-function parity audit.',
        'script':BASE+'check.py','script_sha256':hashed(BASE+'check.py')['sha256'],
        'inputs':[hashed(BASE+x) for x in ('plan.json','run.py','check.py','plot.py')]+[hashed(f'data/pages/lp2-{p:02}.json') for p in (21,22,23,27,28,30)],
        'outputs':[hashed(BASE+x) for x in ('inputs.json','results.json','cases.jsonl','controls.json','reversal.svg')]},
      'visuals':[{'path':BASE+'reversal.svg','caption':'Known-message controls: the archived column reversal restores 112 of 588 planted messages; the separately repaired inverse restores all 588.'}],
      'sources':[{'label':'Pinned Wulfic fractionation script','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/adfgvx_test.py'},
                 {'label':'Pinned Wulfic legacy-method warning','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md'}],
      'related':['wulfic-early-keyspace-diagnostics','lp2-known-vigenere-keys','wulfic-local-codebook-invariants']
    }
    (HERE/'record.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
