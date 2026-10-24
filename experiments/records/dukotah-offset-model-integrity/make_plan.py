"""Freeze exact retrospective evidence inputs for the model-integrity control."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
names=['LICENSE.source','source-lib_padsweep.py','source-skipdecode.py','source-gematria.py',
       'source-lib_l6.py','source-control_offset.py','source-audit_builders.py',
       'source-sweep_offset.py','source-capsule-manifest.json','source-kjv.txt',
       'source-control-offset.json','source-checkpoint-A1-0.json','audit.json',
       'control_offset.json','input-reconstruction.json','pilot-a1.json',
       'corpora-receipt.json','corpus-recovery-check.json','saved-check.json',
       'trigram-kjv-only.npy']
plan={
 'schema':'liberpedia-offset-model-integrity-plan-v1',
 'timing':'Retrospective source-input/control audit after the pinned source outcomes were known; not an independent preregistration of a cipher test.',
 'source_revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1',
 'question':'Can matching control totals establish exact offset screening when two source training books are absent?',
 'scope':'One 40-trial planted offset control and one preselected source A1 unit-0 checkpoint; saved C2 arithmetic is supporting evidence only.',
 'source_model':'Four Gutenberg books: KJV, Moby-Dick, Pride and Prejudice, War and Peace, using GP29 greedy transliteration and a 29x29x29 trigram table.',
 'fallback_model':'Only exact KJV was present when source trigram_model silently skipped missing books. The resulting .npy is included and independently rebuilt.',
 'inputs':[{'path':'experiments/records/dukotah-offset-model-integrity/'+n,
            'sha256':hashlib.sha256((HERE/n).read_bytes()).hexdigest()} for n in names],
 'limitations':['No exact four-book model or Marsaglia pad bytes were recovered.','No full L6 target sweep was rerun or judged negative.','Current Gutenberg Moby/Pride bytes differ from source capsule pins.']}
(HERE/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print('Wrote frozen retrospective plan with',len(names),'hashed inputs')
