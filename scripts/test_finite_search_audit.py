"""Actual JavaScript snapshots audited by the independent Python engine."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_finite_search as audit

NODE = r"""
const fs=require('fs'),crypto=require('crypto'),C=require('./claim-specification.js'),H=require('./claim-share.js'),E=require('./local-experiment.js'),F=require('./finite-search-compiler.js'),Q=require('./finite-program-question.js'),S=require('./finite-search-snapshot.js');
const at='2026-10-25T12:00:00.000Z',f=v=>C.field('specified',v),hash=(v,serialize=E.stable)=>crypto.createHash('sha256').update(serialize(v)).digest('hex');
async function typedFixture(operations,parameters,extraRules={}){const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json'));for(const p of bundle.pages)p.raw='ᚠᚢᚦ ᚩᚱ\nᚠᚢ-ᚦᚩ';const card=H.cardData(C.confirm(C.createDraft({source:{text:'Explicit typed-program parity fixture'},aim:f('Reproduce a result'),method:f({operations}),scope:f({pages:['lp2-15','lp2-16']}),rules:{inputVersion:f('raw'),representation:f('GP29'),evaluation:f({kind:'exact-prefix',values:[28,28]}),searchBounds:f({kind:'finite-settings',version:1,parameters}),...extraRules}}),{id:'fixture',at})),{domain}=await F.compile(card,bundle),sources=[];for(const p of domain.programs){const task=await E.prepare({...p.task,title:'Original typed receipt'}),result=E.run(task);sources.push({task,inputVersion:'raw',run:{id:hash(result),createdAt:at,result}});}const proof=await Q.summarize(domain,sources,{lookupComplete:true});return S.build({proposalId:'p_'+hash(card,C.serialize),card,bundle,domain,proof,sources});}
async function fixture(kind){const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json'));for(const p of bundle.pages)p.raw='ᚠᚢᚠᚢᚦᚩᚱ-ᚠᚢ';const positive=kind==='positive',large=kind==='large',mixed=kind==='mixed',operations=mixed?[{id:'reverse_runes',unit:'line'},{id:'affine',b:0,declaredFamilyId:'fixed-substitution'},{id:'plaintext_autokey',key:[3,1],direction:'subtract'}]:[{id:'affine',label:'Affine substitution',b:0}],parameters=mixed?[{operation:1,name:'a',values:[1,2]},{operation:2,name:'reset',values:['word','page']}]:[{operation:0,name:'a',values:large?Array.from({length:28},(_,i)=>i+1):[1,2]}];if(large){delete operations[0].b;parameters.push({operation:0,name:'b',values:Array.from({length:29},(_,i)=>i)});}const card=H.cardData(C.confirm(C.createDraft({source:{text:'Explicit finite audit fixture'},aim:f('Solve LP2'),method:f({operations}),scope:f({pages:large?['lp2-15']:['lp2-15','lp2-16']}),rules:{inputVersion:f('raw'),representation:f('GP29'),evaluation:f({kind:'exact-prefix',values:positive?[0,1]:[28,28]}),searchBounds:f({kind:'finite-settings',version:1,parameters})}}),{id:'fixture',at})),{domain}=await F.compile(card,bundle),sources=[];let programs=domain.programs;if(kind==='partial')programs=programs.slice(0,1);if(positive)programs=programs.filter(p=>p.task.steps[0].a===1);if(kind==='empty'||large)programs=[];for(const p of programs){const task=await E.prepare({...p.task,title:'Original receipt filed differently'}),result=E.run(task);sources.push({task,inputVersion:'raw',run:{id:hash(result),createdAt:at,result}});}const proof=await Q.summarize(domain,sources,{lookupComplete:!['partial','positive','empty','large'].includes(kind)});return S.build({proposalId:'p_'+hash(card,C.serialize),card,bundle,domain,proof,sources,sourceLinks:sources.map(s=>({taskId:s.task.taskId,href:'run.html#task='+s.task.taskId,label:'Original calculation'}))});}
(async()=>{const out={};for(const kind of ['complete','partial','positive','empty','large','mixed'])out[kind]=await fixture(kind);const typed={};for(const id of ['repeating_key','plaintext_autokey','ciphertext_autokey'])typed[id]=await typedFixture([{id,key:[3,1]}],[{operation:0,name:'direction',values:['subtract','add']},{operation:0,name:'reset',values:['page','line','word']}]);typed.interrupted=await typedFixture([{id:'interrupted_repeating_key',label:'Interrupted repeating key',key:[3,1],direction:'subtract'}],[{operation:0,name:'reset',values:['line','word']},{operation:0,name:'interrupts',values:[[0],[0,1]]}]);typed.finite=await typedFixture([{id:'finite_key',direction:'add'}],[{operation:0,name:'key',values:[Array(12).fill(1),Array(12).fill(3)]},{operation:0,name:'reset',values:['page','word']}]);typed.cumulative=await typedFixture([{id:'cumulative_difference'}],[{operation:0,name:'reset',values:['page','line','word']}],{initialState:f(0)});typed.atbash=await typedFixture([{id:'reverse_runes'},{id:'affine',a:28,b:28}],[{operation:0,name:'unit',values:['page','line','word']}]);typed.row=await typedFixture([{id:'reverse_row_runes'},{id:'affine',a:7}],[{operation:1,name:'b',values:[0,3]}],{wordBoundaries:f('preserve'),boundaryMode:f('within_words')});const nums=[0,0.0,-0,1e-7,1e-6,1e21,0.12345678901234566];process.stdout.write(JSON.stringify({snapshots:out,typed,numbers:nums.map(v=>({value:v,text:E.stable(v)}))}));})().catch(e=>{console.error(e);process.exit(1)});
"""


def resign(snapshot):
    snapshot['snapshotId'] = audit.digest({k: v for k, v in snapshot.items() if k != 'snapshotId'})
    return snapshot


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(['node', '-e', NODE], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
        cls.fixtures = json.loads(result.stdout)

    def snap(self, name='complete'):
        return copy.deepcopy(self.fixtures['snapshots'][name])

    def test_real_cross_language_answers_and_original_hashes(self):
        for kind, answer in [('complete', 'prefix-not-found'), ('partial', 'incomplete'), ('positive', 'prefix-found'), ('empty', 'incomplete'), ('large', 'incomplete'), ('mixed', 'prefix-found')]:
            with self.subTest(kind=kind):
                result = audit.verify(self.snap(kind))
                self.assertEqual(result['finding'], answer)
                self.assertIn('not established as new work', result['limit'])
                self.assertIn('not an offline proof', result['lookupMeaning'])
        self.assertEqual(audit.verify(self.snap('large'))['missingCases'], 812)
        self.assertEqual(audit.verify(self.snap('mixed'))['coveredCases'], 8)

    def test_only_supplied_sources_are_executed_never_missing_cases(self):
        original = audit.runner.run
        calls = []
        def tracked(task):
            calls.append(task['taskId'])
            return original(task)
        audit.runner.run = tracked
        try:
            audit.verify(self.snap('large'))
            self.assertEqual(calls, [])
            audit.verify(self.snap('positive'))
            self.assertEqual(len(calls), 1)
        finally:
            audit.runner.run = original

    def test_all_supported_typed_transformations_and_literal_axes_match_javascript(self):
        for kind, snapshot in self.fixtures['typed'].items():
            with self.subTest(kind=kind):
                result = audit.verify(copy.deepcopy(snapshot))
                self.assertEqual(result['finding'], snapshot['finding']['kind'])
                self.assertEqual(result['missingCases'], 0)
                self.assertEqual(result['coveredCases'], snapshot['question']['totalCases'])
        repeat = self.fixtures['typed']['repeating_key']
        self.assertEqual(len(repeat['question']['programs']), 6)
        # Newline/word boundaries and both arithmetic directions are genuinely
        # exercised, rather than six identities with one accidental output.
        self.assertGreater(len({r['result']['transformed'][0]['text'] for r in repeat['evidence']['results']}), 3)

    def test_snapshot_and_proposal_digests_are_separate(self):
        snapshot = self.snap()
        snapshot['original']['card']['outcome']['value']['detail'] = 'Different intention'
        with self.assertRaisesRegex(ValueError, 'digest'):
            audit.verify(snapshot)
        with self.assertRaisesRegex(ValueError, 'proposal'):
            audit.verify(resign(snapshot))

    def test_declared_settings_cannot_be_replaced_by_a_smaller_self_consistent_program_list(self):
        snapshot = self.snap()
        snapshot['question']['programs'].pop()
        with self.assertRaisesRegex(ValueError, 'exhaust'):
            audit.verify(resign(snapshot))
        snapshot = self.snap()
        snapshot['original']['card']['rules']['searchBounds']['value']['parameters'][0]['values'] = [1, 3]
        snapshot['original']['proposalId'] = 'p_' + audit.digest(snapshot['original']['card'])
        with self.assertRaisesRegex(ValueError, 'exhaust'):
            audit.verify(resign(snapshot))

    def test_exact_input_criterion_version_and_case_identity_remain_bound(self):
        changes = [lambda s: s['question']['pages'][0].update(text='ᚠᚢ'),
                   lambda s: s['question'].update(inputVersion='reviewed'),
                   lambda s: s['question']['criterion'].update(values=[0, 1]),
                   lambda s: s['question']['cases'][0].update(id='f' * 64)]
        for change in changes:
            snapshot = self.snap()
            change(snapshot)
            with self.assertRaises(ValueError):
                audit.verify(resign(snapshot))

    def test_rehashed_forged_output_is_rejected_by_independent_replay(self):
        snapshot = self.snap()
        row = snapshot['evidence']['results'][0]
        old = row['id']
        row['result']['transformed'][0]['text'] = 'ᚠ' * len(row['result']['transformed'][0]['text'])
        row['id'] = audit.digest(row['result'])
        for collection in ('sources', 'caseSources'):
            for source in snapshot['evidence'][collection]:
                if source['resultId'] == old:
                    source['resultId'] = row['id']
        snapshot['evidence']['results'].sort(key=lambda v: v['id'])
        with self.assertRaisesRegex(ValueError, 'replay'):
            audit.verify(resign(snapshot))

    def test_claimed_answer_coverage_and_source_location_cannot_be_relabelled(self):
        changes = [lambda s: s['finding'].update(kind='prefix-found'),
                   lambda s: s['evidence']['coveredCaseIds'].pop(),
                   lambda s: s['evidence']['caseSources'][0].update(createdAt='2020-01-01T00:00:00.000Z'),
                   lambda s: s['evidence']['sourceLocations'][0].update(href='library.html#/experiment/some-record')]
        for change in changes:
            snapshot = self.snap()
            change(snapshot)
            with self.assertRaises(ValueError):
                audit.verify(resign(snapshot))

    def test_unsupported_contracts_and_payload_bounds_fail_closed(self):
        snapshot = self.snap()
        snapshot['original']['card']['rules']['exceptionalCases'] = {'status': 'specified', 'value': 'Skip every seventh rune'}
        snapshot['original']['proposalId'] = 'p_' + audit.digest(snapshot['original']['card'])
        with self.assertRaisesRegex(ValueError, 'condition'):
            audit.verify(resign(snapshot))
        snapshot = self.snap()
        snapshot['extra'] = True
        with self.assertRaisesRegex(ValueError, 'fields'):
            audit.verify(resign(snapshot))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            path.write_text('{"schema":1,"schema":2}', encoding='utf-8')
            with self.assertRaises(ValueError):
                audit.load(path)
            path.write_bytes(b'x' * (audit.MAX_BYTES + 1))
            with self.assertRaisesRegex(ValueError, '8 MiB'):
                audit.load(path)

    def test_rehashed_noncanonical_cards_and_false_integer_aliases_are_rejected(self):
        changes = [lambda c: c.update(version=True),
                   lambda c: c['scope']['value']['pages'].reverse(),
                   lambda c: c['outcome'].update(value={'outcomeId': 'unclassified', 'detail': 'Solve LP2'}),
                   lambda c: c['rules']['searchBounds']['value'].update(version=True),
                   lambda c: c['method']['value'].update(ignored=True),
                   lambda c: c['rules'].update(invented={'status': 'unspecified'})]
        for change in changes:
            snapshot = self.snap()
            change(snapshot['original']['card'])
            snapshot['original']['proposalId'] = 'p_' + audit.digest(snapshot['original']['card'])
            with self.assertRaises(ValueError):
                audit.verify(resign(snapshot))

    def test_js_number_hash_spelling_and_cli_work_without_extra_packages(self):
        for sample in self.fixtures['numbers']:
            self.assertEqual(audit.stable(sample['value']), sample['text'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            path.write_text(json.dumps(self.snap(), ensure_ascii=False), encoding='utf-8')
            done = subprocess.run([sys.executable, str(ROOT / 'tools/verify_finite_search.py'), str(path)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(done.stdout)['finding'], 'prefix-not-found')


if __name__ == '__main__':
    unittest.main()
