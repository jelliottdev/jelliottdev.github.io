"""Offline reproduction of synthetic named-opening snapshots, never manuscript work."""
import base64
import copy
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_finite_search as old
import verify_factored_finite_search as factored


class OfflineOpeningSets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code = r"""
const fs=require('node:fs'),crypto=require('node:crypto'),E=require('./local-experiment.js'),C=require('./claim-specification.js'),H=require('./claim-share.js'),F=require('./finite-search-compiler.js'),Q=require('./finite-program-question.js'),S=require('./finite-search-snapshot.js'),FF=require('./factored-finite-search-compiler.js'),FQ=require('./factored-finite-question.js'),FS=require('./factored-finite-search-snapshot.js'),B=require('./finite-sequence-banks.js');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex'),known=v=>C.field('specified',v),at='2026-10-26T12:00:00.000Z',alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet,encode=v=>v.map(n=>alphabet[n].rune).join(''),criterion={kind:'exact-prefix-set',openings:[{id:'long',values:[0,1,2]},{id:'short',values:[0]},{id:'other',values:[4,5,6]}]},pages=[{id:'lp2-00',raw:encode([0,1,2,3])},{id:'lp2-01',raw:encode([4,5,6])},{id:'lp2-02',raw:'-\n '},{id:'lp2-03',raw:encode([4,5])}];
async function build({bank,partial=false,v1=false,legacy=false,language=false}={}){
 const bundle=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8'));for(const page of pages)Object.assign(bundle.pages.find(p=>p.id===page.id),{raw:page.raw,reviewed_text:page.raw});const operation=bank?{id:'finite_key_bank',bankId:bank.id,bankSha256:bank.sha256,reset:'page',direction:'subtract'}:{id:'affine',b:0},axes=bank?[{operation:0,name:'offset',values:[0,28]}]:[{operation:0,name:'a',values:[1,2]}],evaluation=language?{kind:'language-score',modelId:'gp29-flores-trigram-v1',modelSha256:'8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'}:legacy?{kind:'exact-prefix',values:[0]}:criterion;
 const card=H.cardData(C.confirm(C.createDraft({source:{text:'Synthetic offline opening fixture'},aim:known('Solve LP2'),method:known({operations:[operation]}),scope:known({pages:pages.map(p=>p.id)}),rules:{inputVersion:known('raw'),evaluation:known(evaluation),searchBounds:known({kind:'finite-settings',version:1,parameters:axes})}}),{id:'synthetic',at})),compiler=v1?F:FF,{domain}=await (language?compiler.compileLanguageComparison:compiler.compile)(card,bundle,crypto.webcrypto);
 let tasks;if(v1)tasks=domain.programs.map(p=>p.task);else{const refs=(await FQ.cases(domain,{cursor:0,limit:8})).cases;tasks=(await FQ.select(domain,refs)).cases.map(c=>c.task);}
 if(partial)tasks=tasks.slice(0,1);const sources=tasks.map(task=>{const result=E.run(task);return {task,inputVersion:'raw',run:{id:sha(E.stable(result)),createdAt:at,result}};});
 if(v1){const proof=await Q.summarize(domain,sources,{lookupComplete:true}),snapshot=await S.build({proposalId:'p_'+sha(C.serialize(card)),card,bundle,domain,proof,sources});return {snapshot};}
 const accumulator=language?FQ.createOutputAccumulator(domain):FQ.createAccumulator(domain);await FQ.accept(accumulator,sources);const proof=await FQ.summarize(accumulator,{lookupComplete:true}),files={};async function* stream(){yield* sources;}
 const snapshot=await (language?FS.buildOutputComparison:FS.build)({proposalId:'p_'+sha(C.serialize(card)),card,bundle,domain,proof,sources:stream(),writeChunk:(name,bytes)=>{files[name]=Buffer.from(bytes).toString('base64');}},crypto.webcrypto);return {snapshot,files};
}
(async()=>{const data=JSON.parse(fs.readFileSync('data/finite-sequence-banks.json','utf8')),output={v1:await build({v1:true}),v1partial:await build({v1:true,partial:true}),v2:await build(),v2partial:await build({partial:true}),legacy:await build({v1:true,legacy:true}),banks:[],languageBanks:[]};for(const bank of data.banks){output.banks.push(await build({bank}));output.languageBanks.push(await build({bank,language:true}));}output.bankTails=data.banks.map(bank=>({id:bank.id,sha256:bank.sha256,tails:Array.from({length:29},(_,offset)=>B.resolve(bank.id,bank.sha256,offset))}));console.log(JSON.stringify(output));})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        result = subprocess.run(['node', '-e', code], cwd=ROOT, capture_output=True, text=True, encoding='utf8')
        assert result.returncode == 0, result.stderr
        cls.fixtures = json.loads(result.stdout)

    def audit_factored(self, fixture):
        with tempfile.TemporaryDirectory(prefix='liberpedia-openings-offline-') as folder:
            root = Path(folder)
            for name, encoded in fixture['files'].items():
                file = root / name
                file.parent.mkdir(exist_ok=True, parents=True)
                file.write_bytes(base64.b64decode(encoded))
            return factored.verify(fixture['snapshot'], root)

    def test_v1_and_factored_replay_complete_ordered_openings_empty_and_short(self):
        first = old.verify(self.fixtures['v1']['snapshot'])
        second = self.audit_factored(self.fixtures['v2'])
        self.assertEqual(first['coveredCases'], 8)
        self.assertEqual(second['coveredCases'], 8)
        self.assertEqual(first['matchingCases'], 3)
        self.assertEqual(second['matchingCases'], 3)
        self.assertEqual(first['finding'], second['finding'])
        self.assertEqual(first['finding'], 'prefix-found')
        for result in self.fixtures['v1']['snapshot']['evidence']['results']:
            decisions = result['result']['matches']
            self.assertEqual(next(x for x in decisions if x['page'] == 'lp2-02')['matchingOpenings'], [])
            self.assertEqual(next(x for x in decisions if x['page'] == 'lp2-03')['matchingOpenings'], [])

    def test_partial_set_results_do_not_claim_complete_search_and_never_execute_missing_cases(self):
        for key in ['v1partial', 'v2partial']:
            real = old.runner.run
            recorded = []
            def only_saved(task):
                recorded.append(task['taskId'])
                return real(task)
            with patch.object(old.runner, 'run', side_effect=only_saved):
                result = old.verify(self.fixtures[key]['snapshot']) if key == 'v1partial' else self.audit_factored(self.fixtures[key])
            self.assertEqual(result['finding'], 'incomplete')
            self.assertEqual(len(set(recorded)), result['replayedSources'])
            self.assertGreater(result['matchingCases'], 0)

    def test_all_four_pinned_banks_every_offset_independently_match_js_fulltails(self):
        for bank in self.fixtures['bankTails']:
            for offset, expected in enumerate(bank['tails']):
                self.assertEqual(old.bank_tail(bank['id'], bank['sha256'], offset), expected)
                self.assertEqual(len(expected), 305-offset)
        for fixture in self.fixtures['banks']:
            result = self.audit_factored(fixture)
            self.assertEqual(result['coveredCases'], 8)
            self.assertEqual(result['remainingCases'], 0)

    def test_existing_bank_language_snapshots_replay_with_unchanged_insufficient_semantics(self):
        for fixture in self.fixtures['languageBanks']:
            result = self.audit_factored(fixture)
            self.assertEqual(result['finding'], 'comparisons-complete')
            self.assertEqual(result['coveredCases'], 8)
            self.assertEqual(result['insufficientCases'], 8)

    def test_bank_identity_offset_and_unexpected_card_fields_fail_closed(self):
        bank = self.fixtures['bankTails'][0]
        for identity, sha, offset in [(bank['id'], '0'*64, 0), ('unknown-v1', bank['sha256'], 0), (bank['id'], bank['sha256'], -1), (bank['id'], bank['sha256'], 29), (bank['id'], bank['sha256'], True)]:
            with self.assertRaises(ValueError):
                old.bank_tail(identity, sha, offset)
        card = copy.deepcopy(self.fixtures['banks'][0]['snapshot']['original']['card'])
        operation = copy.deepcopy(card['method']['value']['operations'][0]);operation['offset'] = 0
        for patch_value in [{'bankSha256': '0'*64}, {'offset': 29}, {'skip': 1}, {'key': [0]}, {'label': 'Invented bank'}]:
            with self.assertRaises(ValueError):
                old.compile_steps([{**operation, **patch_value}], card['rules'])

    def test_forged_complete_matching_ids_rejected_even_after_result_and_snapshot_rehash(self):
        snapshot = copy.deepcopy(self.fixtures['v1']['snapshot'])
        entry = next(item for item in snapshot['evidence']['results'] if any(len(row['matchingOpenings']) > 1 for row in item['result']['matches']))
        previous = entry['id']
        next(row for row in entry['result']['matches'] if len(row['matchingOpenings']) > 1)['matchingOpenings'].reverse()
        entry['id'] = old.digest(entry['result'])
        for source in snapshot['evidence']['sources']:
            if source['resultId'] == previous: source['resultId'] = entry['id']
        snapshot['evidence']['results'].sort(key=lambda item: item['id'])
        snapshot['snapshotId'] = old.digest({k:v for k,v in snapshot.items() if k != 'snapshotId'})
        with self.assertRaisesRegex(ValueError, 'independent replay'):
            old.verify(snapshot)

    def test_factored_forged_ordered_names_fail_after_all_hashes_are_recomputed(self):
        fixture = copy.deepcopy(self.fixtures['v2'])
        for reference in fixture['snapshot']['evidence']['chunks']:
            chunk = json.loads(base64.b64decode(fixture['files'][reference['path']]))
            changed = False
            for source in chunk['sources']:
                result = source['run']['result']
                for row in result['matches']:
                    if len(row['matchingOpenings']) > 1:
                        row['matchingOpenings'].reverse()
                        source['run']['id'] = old.digest(result)
                        changed = True
            if changed:
                raw = old.stable(chunk).encode('utf8')
                fixture['files'][reference['path']] = base64.b64encode(raw).decode()
                reference.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        snapshot = fixture['snapshot']
        snapshot['snapshotId'] = old.digest({k:v for k,v in snapshot.items() if k != 'snapshotId'})
        with self.assertRaisesRegex(ValueError, 'independent replay'):
            self.audit_factored(fixture)

    def test_fabricated_derived_opening_set_snapshot_is_rejected(self):
        fixture = copy.deepcopy(self.fixtures['v2'])
        snapshot = fixture['snapshot']
        snapshot['schema'] = 'liberpedia-factored-finite-search-snapshot-v3'
        snapshot['snapshotId'] = old.digest({k:v for k,v in snapshot.items() if k != 'snapshotId'})
        with self.assertRaisesRegex(ValueError, 'Opening sets require direct original results'):
            self.audit_factored(fixture)

    def test_single_prefix_legacy_still_audits_unchanged(self):
        result = old.verify(self.fixtures['legacy']['snapshot'])
        self.assertEqual(result['finding'], 'prefix-found')
        self.assertEqual(result['coveredCases'], 8)


if __name__ == '__main__':
    unittest.main()
