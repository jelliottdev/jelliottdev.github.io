"""Refresh declared hashes for the reviewed source-input control record."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ID='dukotah-offset-model-integrity'
BASE=f'experiments/records/{ID}/'
inputs=['plan.json','check.py','replay.py','plot.py','article.md','LICENSE.source',
        'source-lib_padsweep.py','source-skipdecode.py','source-gematria.py',
        'source-lib_l6.py','source-control_offset.py','source-audit_builders.py',
        'source-sweep_offset.py','source-capsule-manifest.json','source-kjv.txt',
        'source-control-offset.json','source-checkpoint-A1-0.json',
        'audit.json','control_offset.json','input-reconstruction.json',
        'pilot-a1.json','corpora-receipt.json','corpus-recovery-check.json',
        'saved-check.json','trigram-kjv-only.npy',
        'source-run_stats.py','source-lib_numchannel.py',
        'source-b04-ks.py','source-b04-seeds.py',
        'source-b04-results_A.json','source-b04-results_B.json','source-b04-results_C.json',
        'source-kdf.py','source-kdf-results_A.json','source-prng_sweep.py','source-prng-results.json',
        'source-null.py','source-score.py','source-ciphers.py','source-stats.py','source-corpus.py',
        'source-krisyotam_runes.txt','source-english_quadgrams.txt']
outputs=['results.json','comparison.svg']


def info(name):
    return {'path':BASE+name,'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}


r={
 'id':ID,'status':'draft','title':'The offset screen changes when training books are missing',
 'question':'Do matching planted-control totals mean a fallback prefilter selects the same key offsets as the pinned four-book source model?',
 'reader_question':'Can two screens pass the same number of tests but choose different key positions?',
 'reader_finding':'The one-book screen passed the same headline controls as the original, but ranked five of the 40 trials differently. It also selected a different best key position in one search unit.',
 'reader_limit':'This does not reproduce the original four-book search or identify an LP2 key. Two exact training books and the separate random-pad archive remain unavailable.',
 'summary':'Yes. Both kept 26 of 40 planted true offsets, but five individual trial rankings changed; the first-ranked count was 21 versus 22, and one full million-offset target unit chose a different best position.',
 'finding':'The exact source builder/sharding audit passed on locally available inputs. A KJV-only retraining independently rebuilds the fallback trigram cache. Both source and fallback controls recovered 40/40 planted messages and retained 26/40 true offsets; only 35/40 complete trial rows matched. Source ranked the true offset first 21/40 times, fallback 22/40. A1 unit 0 chose offset 400,310 in the archived four-book source checkpoint and 673,662 with the fallback model.',
 'limitations':'This is a retrospective instrument/input control, not an LP2 decryption or a source-exact replay of the full L6 sweep. The pinned Moby-Dick and Pride and Prejudice bytes are absent; their current official downloads fail the capsule hashes, and the 1.2 GB Marsaglia files are absent. The single changed A1 unit does not isolate model drift from every possible environment difference. Archived C2/offset arithmetic was recounted from saved output, not fresh pad scans.',
 'next_steps':'Recover the exact two missing scorer books and Marsaglia bytes, verify their pinned hashes, rebuild the four-book trigram table, then replay the source controls and checkpoint units before extending any target sweep.',
 'outcome':'not-supported',
 'tags':['source input','offset search','prefilter','trigram','planted control','reproducibility'],
 'scope':{
   'pages':[],
   'artifacts':[BASE+'source-lib_padsweep.py',BASE+'source-capsule-manifest.json',BASE+'source-control-offset.json'],
   'representation':'The source 12,956-rune unsolved stream supplies the first 24-rune screening window and 400-rune beam head in one A1 unit; forty source-planted 372-rune English messages test offset recovery. This record makes no page-wide solving claim.',
   'procedure':'Rebuild the fallback 29^3 trigram table independently from pinned KJV; verify four book hash gates; recount paired source/fallback control rows; compare one complete 2^20-offset A1 source checkpoint with a changed-model pilot.',
   'parameters':'40 paired source/fallback planted controls; 1,048,576 offsets in A1 unit 0; GP29, 24-rune screen, 400-rune head, max_skip 8. Archived C2 300-row summaries and offset totals are supporting saved-output arithmetic only.',
   'exclusions':'No exact four-book model reconstruction, no fresh full A1/A2 or Marsaglia sweep, no new negative LP2 key verdict, no general statement that all scorer variants disagree.'},
 'review':{'reviewer':'Independent KJV-only model reconstruction, exact-hash corpus gate, paired row recount and source checkpoint comparison',
           'kind':'source input and decoder control','retested_on':'2026-10-23','human_review':'pending'},
 'reproduction':{'command':f'python -X utf8 {BASE}check.py',
                 'environment':'Python 3 and NumPy; bundled exact KJV, source snapshots, trigram cache and paired receipts. replay.py runs the pinned source in a temporary tree, offline; --controls-only is the shorter run.',
                 'script':BASE+'check.py','script_sha256':info('check.py')['sha256'],
                 'inputs':[info(n) for n in inputs], 'outputs':[info(n) for n in outputs]},
 'visuals':[{'path':BASE+'comparison.svg','caption':'The source and KJV-only screens kept the same number of true offsets while ranking five individual trials differently.'}],
 'sources':[{'label':'Pinned Round 18 offset source','url':'https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round18/L6-offset-marsaglia'},
            {'label':'Pinned Round 19 prefilter audit','url':'https://github.com/Dukotah/cicada3301/tree/f08b20b632d91209ddbaa747e8e2f23df0c78ba1/liber-primus/analysis/round19/C2'}],
 'related':['english-scorer-controls','dukotah-nonenglish-control-gate']}
(HERE/'record.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print('Wrote draft record with',len(inputs),'inputs and',len(outputs),'outputs')
