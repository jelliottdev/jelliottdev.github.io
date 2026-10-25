"""Independent v2 audits of actual factored JS questions and original results."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_factored_finite_search as audit
import verify_finite_search as old

NODE = r"""
const fs=require('fs'),crypto=require('crypto'),C=require('./claim-specification.js'),H=require('./claim-share.js'),E=require('./local-experiment.js'),F=require('./factored-finite-question.js');
const b=JSON.parse(fs.readFileSync('data/local-run-inputs.json')),known=v=>C.field('specified',v),at='2026-10-25T12:00:00.000Z',hash=v=>crypto.createHash('sha256').update(E.stable(v)).digest('hex'),rawhash=v=>crypto.createHash('sha256').update(v).digest('hex');
async function make(kind){const large=kind==='large',positive=kind==='positive',pages=(large?b.pages.filter(p=>/^lp2-(?:[0-4][0-9]|5[0-5])$/.test(p.id)):b.pages.filter(p=>['lp2-15','lp2-16'].includes(p.id))).map(p=>({id:p.id,text:large?p.raw:'ᚠᚢᚦ-ᚩ'})),ops=[{id:'affine',b:0}],parameters=[{operation:0,name:'a',values:large?Array.from({length:28},(_,i)=>i+1):[1,2]}];if(large){delete ops[0].b;parameters.push({operation:0,name:'b',values:Array.from({length:29},(_,i)=>i)});}const criterion={kind:'exact-prefix',values:positive?[0]:Array(12).fill(28)},card=H.cardData(C.confirm(C.createDraft({source:{text:'Explicit factored audit software fixture'},aim:known('Solve LP2'),method:known({operations:ops}),scope:known({pages:pages.map(p=>p.id)}),rules:{inputVersion:known('raw'),representation:known('GP29'),evaluation:known(criterion),searchBounds:known({kind:'finite-settings',version:1,parameters})}}),{id:'fixture',at})),programs=[];if(large){for(let a=1;a<=28;a++)for(let b=0;b<=28;b++)programs.push({steps:[{op:'affine',a,b}]});}else for(let a=1;a<=2;a++)programs.push({steps:[{op:'affine',a,b:0}]});const domain=await F.bind({engine:E.ENGINE,inputVersion:'raw',alphabet:b.alphabet,pages,criterion,programs}),acc=F.createAccumulator(domain),sources=[];if(!large){const refs=(await F.cases(domain)).cases,selected=await F.select(domain,['partial','positive'].includes(kind)?refs.slice(0,1):refs);for(const item of selected.cases){const result=E.run(item.task);sources.push({task:item.task,inputVersion:'raw',run:{id:hash(result),createdAt:at,result}});}if(kind==='aliases')sources.push({...sources[0],run:{...sources[0].run,createdAt:'2026-10-26T12:00:00.000Z'}});for(let i=0;i<sources.length;i+=2)await F.accept(acc,sources.slice(i,i+2));}const checked=await F.summarize(acc,{lookupComplete:kind==='complete'}),chunks=[];for(let i=0;i<sources.length;i+=2){const raw=E.stable({schema:'liberpedia-original-receipt-chunk-v1',sources:sources.slice(i,i+2)});chunks.push({path:'chunks/'+String(chunks.length+1).padStart(6,'0')+'.json',raw});}const proof=Object.fromEntries(['coveredCases','matchingCases','remainingCases','complete','coverageSha256','matchingSha256'].map(k=>[k,checked[k]])),body={schema:'liberpedia-factored-finite-search-snapshot-v2',original:{proposalId:'p_'+hash(card),card},question:domain,evidence:{chunks:chunks.map(c=>({path:c.path,sha256:rawhash(c.raw),bytes:Buffer.byteLength(c.raw),entries:JSON.parse(c.raw).sources.length})),lookup:{recordedComplete:checked.lookupComplete,meaning:LOOKUP},provenanceMeaning:PROVENANCE},proof,finding:{kind:checked.matchingCases?'prefix-found':checked.complete?'prefix-not-found':'incomplete',limit:LIMIT}};return {manifest:{...body,snapshotId:hash(body)},chunks};}
(async()=>{const out={};for(const kind of ['complete','partial','positive','large','aliases'])out[kind]=await make(kind);console.log(JSON.stringify(out));})().catch(e=>{console.error(e);process.exitCode=1;});
"""


class FactoredAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = 'const LOOKUP=' + json.dumps(old.LOOKUP) + ',PROVENANCE=' + json.dumps(old.PROVENANCE) + ',LIMIT=' + json.dumps(old.LIMIT) + ';\n' + NODE
        cls.fixtures = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True, encoding='utf-8'))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='liberpedia-factored-audit-')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, kind='complete'):
        value = copy.deepcopy(self.fixtures[kind])
        for chunk in value['chunks']:
            file = self.root / chunk['path']; file.parent.mkdir(exist_ok=True); file.write_text(chunk['raw'], encoding='utf-8')
        return value['manifest']

    @staticmethod
    def resign(m):
        m['snapshotId'] = old.digest({k: v for k, v in m.items() if k != 'snapshotId'})

    def change_chunk(self, m, mutate, index=0):
        ref = m['evidence']['chunks'][index]; file = self.root / ref['path']; value = json.loads(file.read_text(encoding='utf-8')); mutate(value)
        raw = old.stable(value).encode('utf-8'); file.write_bytes(raw); ref['sha256'] = hashlib.sha256(raw).hexdigest(); ref['bytes'] = len(raw); ref['entries'] = len(value['sources']); self.resign(m)

    def test_real_complete_partial_early_hit_and_actual_dates(self):
        for kind, expected in [('complete', 'prefix-not-found'), ('partial', 'incomplete'), ('positive', 'prefix-found'), ('aliases', 'prefix-not-found')]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                self.root = Path(folder); m = self.write(kind); result = audit.verify(m, self.root)
                self.assertEqual(result['finding'], expected); self.assertEqual(result['domainId'], m['question']['id'])
                self.assertEqual(result['coverageSha256'], m['proof']['coverageSha256'])
                self.assertEqual(result['originalReceipts'], 5 if kind == 'aliases' else 1 if kind in ('partial', 'positive') else 4)
                self.assertEqual(result['replayedSources'], 1 if kind in ('partial', 'positive') else 4)
                self.assertEqual(result['recordedLookupComplete'], kind == 'complete')

    def test_45472_cases_expand_independently_without_running_missing_work(self):
        m = self.write('large'); original = audit.runner.run
        audit.runner.run = lambda task: self.fail('Missing work must not run')
        try:
            result = audit.verify(m, self.root)
        finally:
            audit.runner.run = original
        self.assertEqual(m['question']['totalCases'], 812 * 56); self.assertEqual(result['coveredCases'], 0)
        self.assertEqual(result['remainingCases'], 45472); self.assertEqual(result['finding'], 'incomplete')
        with self.assertRaises(ValueError):
            old.declaration(m['original']['card'])

    def test_semantic_changes_fail_even_when_outer_snapshot_hash_is_recomputed(self):
        for change in [lambda m: m['original']['card']['rules']['searchBounds']['value']['parameters'][0]['values'].pop(),
                       lambda m: m['question']['pages'][0].update(text='ᚠ'),
                       lambda m: m['question']['criterion']['values'].__setitem__(0, 1),
                       lambda m: m['question']['programs'][0]['steps'].append({'op': 'reverse', 'unit': 'word'}),
                       lambda m: m['proof'].update(coverageSha256='0' * 64),
                       lambda m: m['proof'].update(complete=False), lambda m: m['finding'].update(kind='prefix-found')]:
            with self.subTest(change=change):
                m = self.write(); change(m); self.resign(m)
                with self.assertRaises(ValueError): audit.verify(m, self.root)

    def test_original_source_identity_criterion_dates_and_self_hashed_wrong_output_fail(self):
        changes = [lambda s: s['task'].update(title='Rewritten receipt'), lambda s: s.update(inputVersion='reviewed'),
                   lambda s: s['run'].update(createdAt='not-a-date'), lambda s: s['task']['criterion']['values'].__setitem__(0, 0),
                   lambda s: s['run']['result'].update(extra=True)]
        for mutate in changes:
            with self.subTest(mutate=mutate):
                m = self.write(); self.change_chunk(m, lambda c: mutate(c['sources'][0]))
                with self.assertRaises((ValueError, KeyError)): audit.verify(m, self.root)
        m = self.write()
        def forge(c):
            s = c['sources'][0]; other = copy.deepcopy(s['task']); other['steps'] = []; other['taskId'] = old.digest({k: v for k, v in other.items() if k != 'taskId'})
            result = audit.runner.run(other); result['taskId'] = s['task']['taskId']; s['run']['result'] = result; s['run']['id'] = old.digest(result)
        self.change_chunk(m, forge)
        # The chosen affine task may be identity; force an internally changed
        # metric as well so this is unconditionally a forged full result.
        def metrics(c):
            s = c['sources'][0]; s['run']['result']['metrics']['runes'] += 1; s['run']['id'] = old.digest(s['run']['result'])
        self.change_chunk(m, metrics)
        with self.assertRaises(ValueError): audit.verify(m, self.root)

    def test_all_chunks_required_exact_paths_and_raw_hashes(self):
        m = self.write(); first = self.root / m['evidence']['chunks'][0]['path']; first.write_bytes(first.read_bytes() + b' ')
        with self.assertRaises(ValueError): audit.verify(m, self.root)
        m = self.write(); (self.root / 'chunks/999999.json').write_text('{}')
        with self.assertRaises(ValueError): audit.verify(m, self.root)
        (self.root / 'chunks/999999.json').unlink(); first.unlink()
        with self.assertRaises(ValueError): audit.verify(m, self.root)
        m = self.write(); m['evidence']['chunks'][0]['path'] = '../outside.json'; self.resign(m)
        with self.assertRaises(ValueError): audit.verify(m, self.root)

    def test_duplicate_receipts_and_unrecognized_fields_reject(self):
        m = self.write(); self.change_chunk(m, lambda c: c['sources'].__setitem__(1, copy.deepcopy(c['sources'][0])))
        with self.assertRaises(ValueError): audit.verify(m, self.root)
        m = self.write(); self.change_chunk(m, lambda c: c['sources'][0].update(published=True))
        with self.assertRaises(ValueError): audit.verify(m, self.root)
        m = self.write(); m['evidence']['lookup']['meansNoOtherPublicWork'] = True; self.resign(m)
        with self.assertRaises(ValueError): audit.verify(m, self.root)

    def test_totals_reject_before_reading_and_duplicate_json_keys_reject(self):
        m = self.write(); m['evidence']['chunks'][0]['bytes'] = audit.MAX_CHUNK + 1; self.resign(m)
        with self.assertRaises(ValueError): audit.verify(m, self.root)
        with self.assertRaises(ValueError): audit.bounded_json(b'{"a":1,"a":2}', 100)
        m = self.write(); m['evidence']['chunks'] = [{**m['evidence']['chunks'][0], 'path': f'chunks/{i:06d}.json', 'bytes': audit.MAX_CHUNK} for i in range(1, 66)]; self.resign(m)
        with self.assertRaisesRegex(ValueError, 'total'): audit.verify(m, self.root)

    def test_more_than_eight_mib_across_bounded_chunks_preserves_whole_original_receipts(self):
        from datetime import datetime, timedelta
        m = self.write('partial')
        source = json.loads(self.fixtures['partial']['chunks'][0]['raw'])['sources'][0]
        count = (8 * 1024 * 1024) // len(old.stable(source).encode('utf-8')) + 40
        m['evidence']['chunks'] = []
        at = datetime(2026, 10, 25, 12)
        total_bytes = 0
        for first in range(0, count, 12):
            sources = []
            for i in range(first, min(first + 12, count)):
                receipt = copy.deepcopy(source)
                receipt['run']['createdAt'] = (at + timedelta(seconds=i)).isoformat(timespec='milliseconds') + 'Z'
                sources.append(receipt)
            raw = old.stable({'schema': 'liberpedia-original-receipt-chunk-v1', 'sources': sources}).encode('utf-8')
            name = f'chunks/{len(m["evidence"]["chunks"]) + 1:06d}.json'
            (self.root / name).write_bytes(raw)
            m['evidence']['chunks'].append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'entries': len(sources)})
            total_bytes += len(raw)
        self.assertGreater(total_bytes, old.MAX_BYTES)
        self.resign(m)
        result = audit.verify(m, self.root)
        self.assertEqual(result['originalReceipts'], count)
        self.assertEqual(result['replayedSources'], 1)
        self.assertEqual(result['coveredCases'], 1)
        self.assertEqual(result['finding'], 'incomplete')

    def test_coverage_booleans_cannot_impersonate_integer_counts(self):
        m = self.write('partial'); m['proof']['coveredCases'] = True; self.resign(m)
        with self.assertRaisesRegex(ValueError, 'types'):
            audit.verify(m, self.root)

    def test_cli_reads_only_local_manifest_and_chunks(self):
        m = self.write('partial'); filename = self.root / 'manifest.json'; filename.write_text(old.stable(m), encoding='utf-8')
        output = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'tools/verify_factored_finite_search.py'), str(filename)], text=True, encoding='utf-8'))
        self.assertEqual(output['finding'], 'incomplete'); self.assertIn('not an offline proof', output['lookupMeaning'])


if __name__ == '__main__':
    unittest.main()
