"""Write the draft manifest after all scientific artifacts are frozen."""
import hashlib
import json
import pathlib

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
P='experiments/records/wulfic-p21-running-key-layers/'

def item(name):return {'path':P+name,'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}
def rootitem(name):return {'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}

def main():
    record={
      'id':'wulfic-p21-running-key-layers','status':'draft',
      'title':'Deor and Emerson as running keys on ten pages',
      'question':'Do the archived Deor and Self-Reliance running-key or assigned-keyword-plus-running-key sweeps clear their own coincidence gate on LP2-04–13?',
      'reader_question':'Did those two texts work as keys for these pages?',
      'summary':'None of 24,639 source-defined settings passed the program’s normalized coincidence gate. The same gate recovered planted complete messages, including a later independent-key known-reading check.',
      'finding':'The direct sweep tested 12,327 cases and peaked at normalized coincidence 1.148; the keyword-plus-running-key sweep tested 12,312 and peaked at 1.173. Neither reached the source threshold >1.3. All 49 complete within-page-shuffle searches likewise had no gate pass. The unchanged pinned source script, staged with its exact Git blobs under its expected legacy paths, prints no result on all ten pages.',
      'limitations':'The program samples coarse source-text offsets, uses two committed GP-encoded texts and one assigned keyword per page, then rejects anything below a strict whole-page coincidence gate. Nine wordlist-constructed controls are easy for the scorer. Three language diagnostics were post-target and one-page only; the independent known-reading control ranked its correct setting first. Other offsets, keys, editions, boundaries, languages, skip rules and gates are not ruled out.',
      'next_steps':'A new running-key proposal needs a specific text, offset/clock and held-out readable prediction; this source gate did not distinguish the manuscript from 49 page shuffles.',
      'outcome':'inconclusive',
      'tags':['LP2','source replay','running key','layered keyword','Deor','Self-Reliance','index of coincidence'],
      'scope':{
        'pages':[f'lp2-{i:02d}' for i in range(4,14)],
        'artifacts':[P+'plan.json',P+'control-plan-v2.json'],
        'representation':'Exact committed source global P21–30 rune files, each independently aligned with current LP2-04–13; source GP29 greedy encoding of committed Deor and Self-Reliance text.',
        'procedure':'Reconstruct every executed direct running-key and assigned-keyword-plus-running-key offset/mode cell from the pinned program. Check normalized 29×IoC >1.3 before source wordlist scoring. Repeat the entire grid on 49 common seeded page shuffles. Execute the unchanged source in an isolated legacy-path staging tree.',
        'parameters':'12,327 direct and 12,312 layered settings; two committed texts; three decode directions; keyword±running combinations for the layered branch; source offset step max(1,max_offset//200) or //100; 49 controls seed 20261023.',
        'exclusions':'The same program’s autokey-seed branch (already published separately), unsampled offsets, unassigned keywords, other texts or editions, alternate runic alphabets, other scores, interrupted clocks and page ranges.'},
      'review':{'kind':'exact-source bounded replay and source-gate audit','retested_on':'2026-10-23','reviewer':'Unchanged source execution and independent full-grid source-function checker; nine full-message controls; three retrospective one-page language diagnostics with source-function rank verification','human_review':'pending'},
      'reproduction':{
        'command':'python experiments/records/wulfic-p21-running-key-layers/power.py --source-root PATH_TO_PINNED_CHECKOUT --check && python experiments/records/wulfic-p21-running-key-layers/check.py --source-root PATH_TO_PINNED_CHECKOUT && python experiments/records/wulfic-p21-running-key-layers/plot.py --check',
        'environment':'Python 3 standard library; exact public Wulfic Git checkout at bf89d3d13aad2b8f2c95ab195cf1b092f250775c. Upstream unlicensed script and corpora are not redistributed; all necessary Git blobs are SHA-256 verified.',
        'script':P+'check.py','script_sha256':item('check.py')['sha256'],
        'inputs':[item(n) for n in ('plan.json','control-plan.json','control-plan-v2.json','power-addendum-plan.json','power-addendum-v2-plan.json','power-addendum-v3-plan.json','plan.py','run.py','power.py','check.py','plot.py','make_record.py','article.md')]+[rootitem('data/evidence/known-readings.json')],
        'outputs':[item(n) for n in ('controls.json','results.json','power-addendum.json','power-addendum-v2.json','power-addendum-v3.json','source-log.txt','gate.svg')]},
      'visuals':[{'path':P+'gate.svg','caption':'Neither source branch reached its own first screen on LP2-04–13; complete planted messages show that the gate can pass.'}],
      'sources':[{'label':'Pinned Wulfic P21–30 source program','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p21_30_autokey_solver.py'},
                 {'label':'Pinned legacy caveat','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md'}],
      'related':['wulfic-autokey-seed-families','emerson-running-key','solved-reading-running-key']}
    (HERE/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print('record manifest written')

if __name__=='__main__':main()
