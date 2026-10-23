"""Hash the frozen grouped source replay into a draft record."""
import hashlib
import json
import pathlib
HERE=pathlib.Path(__file__).resolve().parent
P='experiments/records/wulfic-p21-rearrangement-routes/'
def item(name):return {'path':P+name,'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}

def main():
    obj={
      'id':'wulfic-p21-rearrangement-routes','status':'draft',
      'title':'What the archived P21–30 rearrangements could score',
      'question':'What changes under the exact 45 keyword-then-rearrangement routes in the archived P21–30 program, and does its best word score stand out from complete shuffled searches?',
      'reader_question':'Could rearranging these keyword-decoded pages reveal a reading?',
      'summary':'The top source word score, 111, was met or beaten by 85 of 199 complete shuffled searches. Most routes cannot change the metric used to judge them: complete permutations preserve coincidence, word-order changes preserve word score, and the source scores character routes without spaces.',
      'finding':'The exact source runs 45 routes on each of ten matched LP2-04–13 pages. All 390 full-length routes preserve the decoded-page rune histogram and normalized IoC; all 50 whole-word-order trials preserve the original dictionary score. All 380 character-level outputs score zero under the source unspaced whole-word dictionary check, while a full-message reverse-route plant scores 1,266 with spaces and zero through that unspaced path. Best target score is 111; 85/199 shuffled full searches meet or exceed it.',
      'limitations':'The archived keywords are proposals. The 60 shortened position extractions do not preserve full-page frequency, although they too score zero as unspaced strings here. The source scoring path cannot fairly judge a multiword reading after character-level rearrangement; zero scores are not evidence against those routes. The 199 shared page shuffles are a retrospective descriptive reference, not a cipher model. Other keywords, routes, segmentations and languages are open.',
      'next_steps':'Specify a route with an invertible construction and preserve or recover word boundaries before using dictionary score as a reading test. Check an untouched passage after choosing the key and route.',
      'outcome':'inconclusive',
      'tags':['LP2','source replay','transposition','prime positions','Fibonacci positions','word order','scoring limitation'],
      'scope':{
        'pages':[f'lp2-{i:02d}' for i in range(4,14)],
        'artifacts':[P+'plan.json'],
        'representation':'Exact committed Wulfic source rune files for old pages21–30 aligned with current LP2-04–13, its fixed page keyword vectors and its committed 370,079-entry wordlist.',
        'procedure':'Execute all 45 called source route outputs for each page, preserving branch-specific spacing and the source dictionary scorer. Check frequency and word-order invariants, complete reverse-route planted recovery, and 199 seeded whole-grid within-page shuffle searches.',
        'parameters':'450 source rows; 390 full-length route rows, 60 shortened extract rows; 199 complete shared-corpus shuffles seed 20261023.',
        'exclusions':'A separate source file transposition_solver.py is covered elsewhere. This replay does not test uncalled source helpers, arbitrary keyword or route invention, alternate transcriptions, a better language scorer or cross-page routes.'},
      'review':{'kind':'exact-source bounded replay and scorer-power audit','retested_on':'2026-10-23','reviewer':'Unchanged source execution; independent reconstruction of all 450 rows, 199 shuffled full-search maxima and planted full-message route; exact source/site rune parity','human_review':'pending'},
      'reproduction':{
        'command':'python experiments/records/wulfic-p21-rearrangement-routes/run.py --source-root PATH_TO_PINNED_CHECKOUT --check && python experiments/records/wulfic-p21-rearrangement-routes/check.py --source-root PATH_TO_PINNED_CHECKOUT && python experiments/records/wulfic-p21-rearrangement-routes/plot.py --check',
        'environment':'Python 3 standard library; exact public Wulfic Git checkout at bf89d3d13aad2b8f2c95ab195cf1b092f250775c. Its script and unlicensed wordlist are SHA-256 verified at execution and not redistributed.',
        'script':P+'check.py','script_sha256':item('check.py')['sha256'],
        'inputs':[item(n) for n in ('plan.json','plan.py','run.py','check.py','plot.py','make_record.py','article.md')],
        'outputs':[item(n) for n in ('results.json','source-log.txt','route-summary.svg')]},
      'visuals':[{'path':P+'route-summary.svg','caption':'Which route outcomes are structurally unchanged, and how the top source word score compares with 199 complete shuffled searches.'}],
      'sources':[{'label':'Pinned P21–30 rearrangement source','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/p21_30_rearrange.py'},
                 {'label':'Pinned legacy-method caveat','url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md'}],
      'related':['wulfic-keyed-transposition-cohort','lp2-row-column-routes','wulfic-p21-running-key-layers']}
    (HERE/'record.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print('record manifest written')
if __name__=='__main__':main()
