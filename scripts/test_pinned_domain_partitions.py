"""Independent detached planner parity; no controls or manuscript programs run."""
import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
import build_repeating_key_banks as banks
import pinned_domain_partitions as planner


class Registry:
    def __init__(self):
        self.keys = [[i % 29, (i // 29) % 29, i // 841] + ([0] * 321 if i >= 2237 else []) for i in range(2561)]
        self.metadata = dict(id='synthetic-large-domain', sha256=planner.digest(self.keys), total=2561, sourcePins=[dict(path='test/synthetic.json', sha256=hashlib.sha256(b'synthetic').hexdigest())])
        self.calls = []

    def list(self):
        return [copy.deepcopy(self.metadata)]

    def resolve(self, ref):
        self.calls.append(copy.deepcopy(ref))
        return copy.deepcopy(self.keys[ref['start']:ref['start'] + ref['count']])


def fixture(synthetic=False):
    registry = Registry() if synthetic else planner.MaintainedRegistry()
    metadata = registry.metadata if synthetic else registry.list()[1]
    openings = json.loads((banks.ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json').read_bytes())['openings']
    domain = dict(schema=planner.SCHEMA, aim=dict(outcomeId='decipher', detail='Try the declared complete key schedule against fixed openings'), bank=dict(bankId=metadata['id'], bankSha256=metadata['sha256'], start=0, count=metadata['total']), keyOperation=1,
                  steps=[dict(op='reverse', unit='word'), dict(op='keyed-shift', mode='repeat', direction='subtract', reset='page'), dict(op='affine', a=28, b=28)],
                  inputVersion='raw', pages=[dict(id='lp2-%02d' % i, textSha256=hashlib.sha256(('official-source-pin-' + str(i)).encode()).hexdigest()) for i in range(56) if i != 50],
                  alphabetSha256=planner.ALPHABET, criterion=dict(kind='exact-prefix-set', openings=[dict(id=o['id'], values=o['indices']) for o in openings]), sourcePins=copy.deepcopy(metadata['sourcePins']))
    return domain, registry


def real_fixture(variant):
    domain, registry = fixture()
    metadata = next(b for b in registry.list() if b['id'] == 'public-wordlist-' + variant + '-v1')
    domain['bank'] = dict(bankId=metadata['id'], bankSha256=metadata['sha256'], start=0, count=metadata['total'])
    domain['sourcePins'] = copy.deepcopy(metadata['sourcePins'])
    domain['steps'] = [dict(op='keyed-shift', mode='repeat', direction='subtract', reset='page')]
    domain['keyOperation'] = 0
    source_pages = {p['id']: p['raw'] for p in json.loads((banks.ROOT / 'data/local-run-inputs.json').read_bytes())['pages']}
    domain['pages'] = [dict(id=p['id'], textSha256=hashlib.sha256(source_pages[p['id']].encode()).hexdigest()) for p in domain['pages']]
    return domain


class PinnedDomainPartitions(unittest.TestCase):
    def test_maintained_complete_bank_preserves_declaration_and_exact_nonresult_counters(self):
        domain, registry = fixture()
        before = copy.deepcopy(domain)
        result = planner.prepare(domain, registry)
        self.assertEqual(result['domain'], domain)
        self.assertEqual(domain, before)
        self.assertEqual(result['status'], 'planning-only')
        self.assertEqual(result['checks'], dict(admission=False, execution=False, controlBudget=False))
        self.assertEqual(result['counters'], dict(programs=309, pages=55, pageCases=16995, openingComparisons=152955))
        self.assertEqual(result['domainId'], 'd_' + planner.digest(domain))
        self.assertEqual(planner.validate(domain, result, registry), result)
        result['domain']['steps'][0]['unit'] = 'line'
        self.assertEqual(domain['steps'][0]['unit'], 'word')

    def test_aim_is_explicit_retained_and_changes_parent_identity_independently_of_criterion(self):
        domain, registry = fixture()
        before = planner.prepare(domain, registry)
        for outcome in ('decipher', 'measure', 'reproduce', 'explain', 'verify_source'):
            d = copy.deepcopy(domain)
            d['aim'] = dict(outcomeId=outcome, detail='A declared aim')
            result = planner.prepare(d, registry)
            self.assertEqual(result['domain']['aim'], d['aim'])
            self.assertNotEqual(result['domainId'], before['domainId'])
            self.assertEqual(result['domain']['criterion'], before['domain']['criterion'])
        changed_detail = copy.deepcopy(domain)
        changed_detail['aim']['detail'] = 'A different detail for the same essential aim'
        self.assertNotEqual(planner.prepare(changed_detail, registry)['domainId'], before['domainId'])
        for aim in (None, dict(outcomeId='unknown', detail='text'), *[dict(outcomeId='decipher', detail=x) for x in ('', ' text', 'a' * 1001, 'bad\ntext', 'bad\u202etext')], dict(outcomeId='decipher', detail='text', extra=True)):
            d = copy.deepcopy(domain)
            d['aim'] = aim
            with self.assertRaises(ValueError):
                planner.prepare(d, registry)
        domain['aim']['detail'] = '😀' * 1000
        self.assertEqual(planner.prepare(domain, registry)['domain']['aim'], domain['aim'])

    def test_full_large_domain_keeps_every_oversized_vector_and_exact_contiguous_ranges(self):
        domain, registry = fixture(True)
        result = planner.prepare(domain, registry)
        self.assertEqual([(j['bank']['start'], j['bank']['count']) for j in result['jobs']], [(0, 1024), (1024, 1024), (2048, 513)])
        self.assertEqual(result['telemetry'], dict(maxKeyLength=324, overRepeatingKeyLimit=324))
        self.assertEqual(result['counters']['programs'], 2561)
        self.assertEqual(result['counters']['pageCases'], 140855)
        self.assertEqual(result['counters']['openingComparisons'], 1267695)
        self.assertEqual(sum(c['count'] for c in registry.calls), 2561)
        self.assertTrue(all(c['count'] <= 1024 for c in registry.calls))
        for job in result['jobs']:
            self.assertEqual(job['id'], 'j_' + planner.digest(dict(schema='liberpedia-pinned-domain-slice-id-v1', domainId=result['domainId'], range={k: job['bank'][k] for k in ('start', 'count')})))

    def test_all_declared_pins_operations_criteria_and_bank_completeness_are_required(self):
        changes = [lambda d: d['bank'].update(start=1), lambda d: d['bank'].update(count=1), lambda d: d['bank'].update(bankSha256='0' * 64),
                   lambda d: d['sourcePins'].pop(), lambda d: d['pages'].append(copy.deepcopy(d['pages'][0])), lambda d: d['steps'][1].update(key=[1]),
                   lambda d: d.update(keyOperation=0), lambda d: d.update(criterion=dict(kind='readability')), lambda d: d.update(extra=True),
                   lambda d: d['sourcePins'][0].update(path='../escape.json'), lambda d: d['steps'][0].update(unit='unknown'), lambda d: d['pages'][0].update(textSha256='invalid')]
        for change in changes:
            domain, registry = fixture()
            change(domain)
            with self.assertRaises(ValueError):
                planner.prepare(domain, registry)

    def test_coerced_regex_scalars_and_terminal_newlines_reject_with_javascript_parity(self):
        domain, registry = fixture()
        bad_domains = []
        for path in (('pages', 0, 'id'), ('pages', 0, 'textSha256'), ('sourcePins', 0, 'sha256'), ('sourcePins', 0, 'path'), ('bank', 'bankSha256'), ('bank', 'bankId'), ('criterion', 'openings', 0, 'id')):
            for transform in (lambda v: [v], lambda v: v + '\n', lambda v: 42):
                d = copy.deepcopy(domain)
                parent = d
                for k in path[:-1]:
                    parent = parent[k]
                parent[path[-1]] = transform(parent[path[-1]])
                bad_domains.append(d)
                with self.assertRaises(ValueError):
                    planner.prepare(d, registry)
        unicode_page = copy.deepcopy(domain)
        unicode_page['pages'][0]['id'] = 'lp2-0\u0660'
        bad_domains.append(unicode_page)
        with self.assertRaises(ValueError):
            planner.prepare(unicode_page, registry)
        code = "const P=require('./pinned-domain-partitions.js'),fs=require('fs');(async()=>{for(const d of JSON.parse(fs.readFileSync(0,'utf8'))){let rejected=false;try{await P.prepare(d,{crypto:require('crypto').webcrypto});}catch(e){rejected=true;}if(!rejected)throw Error('Coerced identity accepted');}process.stdout.write('all rejected');})().catch(e=>{console.error(e);process.exitCode=1;});"
        result = subprocess.run(['node', '-e', code], input=json.dumps(bad_domains), encoding='utf-8', capture_output=True, cwd=banks.ROOT, check=True)
        self.assertEqual(result.stdout, 'all rejected')

    def test_missing_duplicate_or_invalid_bank_vectors_cannot_be_hidden_by_count_totals(self):
        for mode in ('short', 'duplicate', 'invalid', 'extra'):
            domain, registry = fixture(True)
            original = registry.resolve
            def altered(ref):
                keys = original(ref)
                if mode == 'short':
                    keys.pop()
                elif mode == 'duplicate':
                    keys[1] = keys[0][:]
                elif mode == 'invalid':
                    keys[0][0] = 29
                else:
                    keys.append([1])
                return keys
            registry.resolve = altered
            with self.assertRaises(ValueError):
                planner.prepare(domain, registry)

    def test_plan_and_original_input_mutations_are_rejected(self):
        domain, registry = fixture(True)
        result = planner.prepare(domain, registry)
        for change in [lambda p: p['checks'].update(admission=True), lambda p: p['jobs'][0]['bank'].update(count=1), lambda p: p['counters'].update(pageCases=0), lambda p: p['domain']['steps'].reverse()]:
            bad = copy.deepcopy(result)
            change(bad)
            with self.assertRaises(ValueError):
                planner.validate(domain, bad, registry)
        original = registry.resolve
        def mutate(ref):
            domain['steps'][0]['unit'] = 'line'
            return original(ref)
        registry.resolve = mutate
        with self.assertRaisesRegex(ValueError, 'changed'):
            planner.prepare(domain, registry)

    def test_real_rotating_domains_default_registry_complete_parity(self):
        import time
        code = "const P=require('./pinned-domain-partitions.js'),fs=require('fs');P.prepare(JSON.parse(fs.readFileSync(0,'utf8')),{crypto:require('crypto').webcrypto}).then(p=>process.stdout.write(JSON.stringify(p))).catch(e=>{console.error(e);process.exitCode=1;});"
        for variant in ('rotate-left', 'rotate-right'):
            domain = real_fixture(variant)
            begin = time.perf_counter()
            result = planner.prepare(domain)
            elapsed = time.perf_counter() - begin
            process = subprocess.run(['node', '-e', code], input=json.dumps(domain), encoding='utf-8', capture_output=True, cwd=banks.ROOT, check=True)
            self.assertEqual(result, json.loads(process.stdout))
            self.assertEqual([(j['bank']['start'], j['bank']['count']) for j in result['jobs']], [(0, 1024), (1024, 1024), (2048, 513)])
            self.assertEqual(result['telemetry'], dict(maxKeyLength=324, overRepeatingKeyLimit=324))
            self.assertEqual(result['counters'], dict(programs=2561, pages=55, pageCases=140855, openingComparisons=1267695))
            print('Real %s default Python plan: %.3fs; exact JavaScript parity; no execution/admission' % (variant, elapsed))

    def test_default_registry_authenticates_once_and_returns_detached_slices(self):
        from unittest.mock import patch
        domain = real_fixture('rotate-right')
        with patch.object(banks, 'prepare', wraps=banks.prepare) as authenticated:
            registry = planner.MaintainedRegistry()
            metadata = registry.list()[-1]
            ref = dict(bankId=metadata['id'], bankSha256=metadata['sha256'], start=0, count=128)
            first = registry.resolve(ref)
            first[0][0] = 99
            self.assertNotEqual(registry.resolve(ref)[0][0], 99)
            registry.list()[0]['total'] = -1
            self.assertEqual(registry.list()[0]['total'], 43)
            planner.prepare(domain, registry)
            self.assertEqual(authenticated.call_count, 1)
            for bad in ({**ref, 'count': 1025}, {**ref, 'start': True}, {**ref, 'bankSha256': '0' * 64}, {**ref, 'extra': 1}):
                with self.assertRaises(ValueError):
                    registry.resolve(bad)

    def test_actual_javascript_python_complete_plan_and_ids_match(self):
        code = "const P=require('./pinned-domain-partitions.js'),fs=require('fs');const v=JSON.parse(fs.readFileSync(0,'utf8')),registry=v.keys?{list:()=>[v.metadata],resolve:r=>v.keys.slice(r.start,r.start+r.count)}:undefined;P.prepare(v.domain,{registry,crypto:require('crypto').webcrypto}).then(p=>process.stdout.write(JSON.stringify(p))).catch(e=>{console.error(e);process.exitCode=1;});"
        for synthetic in (False, True):
            domain, registry = fixture(synthetic)
            payload = dict(domain=domain)
            if synthetic:
                payload.update(metadata=registry.metadata, keys=registry.keys)
            process = subprocess.run(['node', '-e', code], input=json.dumps(payload), encoding='utf-8', capture_output=True, cwd=banks.ROOT, check=True)
            self.assertEqual(json.loads(process.stdout), planner.prepare(domain, registry))


if __name__ == '__main__':
    unittest.main()
