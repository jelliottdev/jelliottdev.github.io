"""Write the draft site record after scientific outputs are frozen."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];ID=P.name;BASE=f'experiments/records/{ID}/'
def hashed(rel):return {'path':rel,'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()}
def main():
    rec={
      'id':ID,'status':'draft','title':'Can word cribs predict a periodic key?',
      'question':'Does the source word-vote solver at its page_30/period-17 and page_27/period-43 examples recover exact words it did not use to infer the key?',
      'reader_question':'Can familiar words reveal a repeating key?',
      'summary':'The archived word-vote solver produces no exact dictionary words in any untouched LP2 fold. It also fails the predeclared known-message gate, so this result does not rule out periodic-key ciphers.',
      'finding':'Archived page_30 and page_27 correspond exactly to current LP2-13 and LP2-10. Across both pages, both alternating-word folds and all three directions, zero untouched words match an encoded source dictionary word. The source full-stream scores of 10–19 count substrings, not recovered words. Twelve planted periodic-key folds recover at most 11 of roughly 30 untouched words, below the fixed 50% gate; no null-rank exclusion follows.',
      'limitations':'The source solver votes for each residue separately and enforces only within-word consistency, despite its description of cross-word consistency. The two periods are source examples rather than detected cycles. The 199-shuffle selected maximum is retained as a receipt but not interpreted because the positive gate fails. Missing public GPU checkpoint prevents reproduction of four related validators.',
      'next_steps':'A new candidate should state its page, period, clock, direction, crib list and a held-out plaintext prediction before examining the remaining words.',
      'outcome':'inconclusive','tags':['LP2','source-derived test','periodic key','crib dragging','word boundaries','positive control'],
      'scope':{'pages':['lp2-10','lp2-13'],'artifacts':[BASE+'plan.json'],
        'representation':'Pinned source page_27 and page_30 rune files, byte-checked against site LP2-10 and LP2-13. Source GP29 encoder and exact 335-entry dictionary (309 distinct encoded words).',
        'procedure':'Replay original word-vote keys and source stdout on the two example page/period pairs. Separately train on alternating visible word slots, score exact dictionary words on untouched slots, run 12 planted known-message folds and 199 matched whole-selection shuffles.',
        'parameters':'Source periods 43 and 17; SUB, ADD, BEAUFORT; visible 2–15-rune words; source-insertion-order vote ties; two train/holdout folds; 199 shuffles seeded 33014317.',
        'exclusions':'Other pages, periods, dictionaries, language hypotheses, page-spanning clocks, the checkpoint-dependent validator scripts, linked-position phrase crib script, and a family-wide cipher rejection.'},
      'review':{'kind':'exact source replay plus bounded held-out extension','retested_on':'2026-10-23','reviewer':'Pinned source dictionary and page bytes; six source keys and twelve held-out folds independently checked; predeclared planted gate failed and null rank withheld','human_review':'pending'},
      'reproduction':{'command':f'python {BASE}run.py --source-root PATH_TO_PINNED_CLONE --check',
        'environment':'Python 3 standard library and Git checkout at pinned Wulfic revision; local site page JSON.',
        'script':BASE+'check.py','script_sha256':hashed(BASE+'check.py')['sha256'],
        'inputs':[hashed(BASE+n) for n in ('plan.json','run.py','check.py','plot.py')]+[hashed(f'data/pages/lp2-{p:02}.json') for p in (10,13)],
        'outputs':[hashed(BASE+n) for n in ('summary.json','dictionary.json','source_runs.json','observed.json','plants.json','null.json','heldout.svg')]},
      'visuals':[{'path':BASE+'heldout.svg','caption':'The voted key predicts no exact dictionary words in untouched LP2 slots. It also fails the known-message control.'}],
      'sources':[{'label':'Pinned Wulfic period-constrained crib solver','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/period_crib_solve.py'},
        {'label':'Pinned Wulfic legacy-method warning','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md'}],
      'related':['periodic-affine-crib-capacity','wulfic-periodic-alphabet-lags']}
    (P/'record.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
