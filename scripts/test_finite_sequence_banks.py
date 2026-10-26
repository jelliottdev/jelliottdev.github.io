"""Independent finite bank vectors, complete source audit and browser parity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import build_finite_sequence_banks as builder
import finite_sequence_banks as banks

ROOT = banks.ROOT


class FiniteSequenceBanks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = [ROOT / 'experiments/records' / record / name
                     for record, (_, pins) in builder.SOURCE_PINS.items() for name in pins]
        cls.before = {path: path.read_bytes() for path in cls.paths}
        cls.value = builder.build()

    def test_full_source_audit_all_arrays_decisions_and_original_bytes(self):
        audit = self.value['sourceAudit']
        self.assertEqual(audit['archivedArrays'], 12760)
        self.assertEqual(audit['openingComparisons'], 114840)
        self.assertEqual(len(audit['sources']), 4)
        for source in audit['sources']:
            self.assertEqual(source['archivedArrays'], 3190)
            self.assertEqual(source['openingComparisons'], 28710)
            self.assertEqual(source['openingMatches'], 0)
            self.assertEqual(source['namedOffsets'], list(range(29)))
            self.assertEqual(source['maximumPageRunes'], 277)
            self.assertEqual(source['emptyPages'], ['lp2-50'])
            self.assertEqual(len(source['openings']), 9)
            self.assertEqual(source['bankTerms'], 305)
        for path, before in self.before.items():
            self.assertEqual(path.read_bytes(), before)

    def test_raw_sequences_independently_match_complete_vectors_and_pins(self):
        for bank in self.value['banks']:
            actual = banks.get(bank['id'], bank['sha256'])
            self.assertEqual(actual, bank)
            self.assertEqual(actual['values'], [n % 29 for n in builder.raw_sequence(bank['id'])])
            self.assertEqual(banks.bank_hash(bank['id'], bank['values']), banks.PINS[bank['id']])
            self.assertEqual(len(actual['values']), 305)
            for offset in range(29):
                tail = banks.resolve(bank['id'], bank['sha256'], offset)
                self.assertEqual(tail, bank['values'][offset:])
                self.assertEqual(len(tail), 305 - offset)
                self.assertGreaterEqual(len(tail), 277)
            actual['values'][0] = (actual['values'][0] + 1) % 29
            self.assertEqual(banks.get(bank['id'], bank['sha256']), bank)

    def test_fibonacci_named_aliases_preserve_distinct_full_tails(self):
        bank = banks.get('fibonacci-v1', banks.PINS['fibonacci-v1'])
        audit = next(s for s in self.value['sourceAudit']['sources'] if s['bankId'] == bank['id'])
        self.assertEqual(len(audit['fibonacciAliases']), 29)
        for alias in audit['fibonacciAliases']:
            offset = alias['offset']
            base = alias['equivalentOffsetWithinAudited277Runes']
            self.assertEqual(bank['values'][offset:offset + 277], bank['values'][base:base + 277])
        self.assertNotEqual(banks.resolve(bank['id'], bank['sha256'], 0),
                            banks.resolve(bank['id'], bank['sha256'], 14),
                            'Equivalent audited prefixes do not authorize replacing named full finite tails')

    def test_unknown_hash_offset_and_manifest_tampering_fail_closed(self):
        for identifier, pin in banks.PINS.items():
            for offset in (-1, 29, True, 1.0, '1', None):
                with self.assertRaises(ValueError):
                    banks.resolve(identifier, pin, offset)
            with self.assertRaises(ValueError):
                banks.get(identifier, '0' * 64)
        with self.assertRaises(ValueError):
            banks.get('unknown-v1', '0' * 64)
        original = Path.read_bytes
        path = ROOT / 'data/finite-sequence-banks.json'
        for mutation in ('value', 'hash', 'missing', 'extra', 'bool'):
            bad = copy.deepcopy(self.value)
            if mutation == 'value':
                bad['banks'][0]['values'][0] = (bad['banks'][0]['values'][0] + 1) % 29
            elif mutation == 'hash':
                bad['banks'][0]['sha256'] = '0' * 64
            elif mutation == 'missing':
                bad['banks'].pop()
            elif mutation == 'extra':
                bad['banks'][0]['extra'] = True
            else:
                bad['banks'][0]['values'][0] = True
            def injected(p):
                return banks.stable(bad).encode() if p == path else original(p)
            with self.subTest(mutation=mutation), patch.object(Path, 'read_bytes', injected):
                with self.assertRaises(ValueError):
                    banks.get('prime-minus-one-v1', banks.PINS['prime-minus-one-v1'])

    def test_frozen_source_scripts_plan_results_and_inputs_are_pinned(self):
        original = Path.read_bytes
        record = 'lp2-prime-minus-one-openings'
        folder = ROOT / 'experiments/records' / record
        paths = [folder / name for name in builder.SOURCE_PINS[record][1]] + [ROOT / 'text/lp2-00.txt']
        for changed in paths:
            def injected(path):
                raw = original(path)
                return raw + b' ' if path == changed else raw
            with self.subTest(path=changed.name), patch.object(Path, 'read_bytes', injected):
                with self.assertRaises(ValueError):
                    builder.audit_source(record)

    def test_freshly_repinned_malformed_source_is_independently_rejected(self):
        original = Path.read_bytes
        record = 'lp2-prime-minus-one-openings'
        path = ROOT / 'experiments/records' / record / 'results.json'
        source = json.loads(original(path))
        for mutation in ('raw-sequence', 'output-rune', 'decision', 'counter', 'missing-case'):
            bad = copy.deepcopy(source)
            if mutation == 'raw-sequence':
                bad['shifts'][0] += 1
            elif mutation == 'output-rune':
                bad['cases'][0]['output_indices'][0] = (bad['cases'][0]['output_indices'][0] + 1) % 29
            elif mutation == 'decision':
                bad['cases'][0]['matching_openings'] = ['warning']
            elif mutation == 'counter':
                bad['comparison_count'] += 1
            else:
                bad['cases'].pop()
            raw = banks.stable(bad).encode()
            identifier, pins = builder.SOURCE_PINS[record]
            pins = {**pins, 'results.json': hashlib.sha256(raw).hexdigest()}
            def injected(p):
                return raw if p == path else original(p)
            with self.subTest(mutation=mutation), patch.object(Path, 'read_bytes', injected), \
                    patch.dict(builder.SOURCE_PINS, {record: (identifier, pins)}):
                with self.assertRaises(ValueError):
                    builder.audit_source(record)

    def test_javascript_python_bank_tail_parity_and_literal_corruption(self):
        script = """
const fs=require('fs'),vm=require('vm'),B=require('./finite-sequence-banks.js'),data=JSON.parse(fs.readFileSync('data/finite-sequence-banks.json','utf8'));
const values=data.banks.map(bank=>({descriptor:B.get(bank.id,bank.sha256),tails:Array.from({length:29},(_,i)=>B.resolve(bank.id,bank.sha256,i))}));
for(const bank of data.banks){for(const offset of [-1,29,true,1.5,'1',null]){let failed=false;try{B.resolve(bank.id,bank.sha256,offset)}catch{failed=true}if(!failed)throw Error('Invalid offset accepted');}let failed=false;try{B.get(bank.id,'0'.repeat(64))}catch{failed=true}if(!failed)throw Error('Changed pin accepted');const altered=B.get(bank.id,bank.sha256);altered.values[0]=99;if(B.get(bank.id,bank.sha256).values[0]===99)throw Error('Mutable bank');}
const text=fs.readFileSync('finite-sequence-banks.js','utf8'),broken=text.replace('"values":[1,2,4,6', '"values":[0,2,4,6');if(broken===text)throw Error('Tamper fixture did not change literal');let rejected=false;try{vm.runInNewContext(broken,{TextEncoder})}catch{rejected=true}if(!rejected)throw Error('Corrupted literal accepted');
console.log(JSON.stringify(values));
"""
        actual = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, encoding='utf8'))
        self.assertEqual(len(actual), 4)
        for bank, item in zip(self.value['banks'], actual):
            self.assertEqual(item['descriptor'], banks.get(bank['id'], bank['sha256']))
            self.assertEqual(item['tails'], [banks.resolve(bank['id'], bank['sha256'], n) for n in range(29)])


if __name__ == '__main__':
    unittest.main()
