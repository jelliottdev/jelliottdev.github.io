"""Lossless pooled-control parity and resource boundaries, without execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import finite_control_storage as codec

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(codec.stable(value).encode('utf8')).hexdigest()


def recipes():
    found = []
    for path in sorted((ROOT / 'experiments/records').glob('*/record.json')):
        record = json.loads(path.read_bytes())
        found.extend((record['id'], r) for r in record.get('browser_followups', []) if r.get('kind') == 'finite-settings')
    return found


class PooledControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = recipes()
        cls.source = codec.expand(cls.sources[0][1]['control'])
        cls.single = copy.deepcopy(cls.source)
        cls.single['members'] = cls.single['members'][:1]

    def test_all17_sources_roundtrip_default_compatibility_and_javascript_exact_format(self):
        self.assertEqual(len(self.sources), 17)
        expected = []
        controls = []
        for identifier, recipe in self.sources:
            source = recipe['control']
            before = digest(source)
            legacy = codec.expand(source)
            pooled = codec.compact_pooled(source)
            self.assertEqual(pooled['kind'], codec.POOLED)
            self.assertEqual(codec.expand(pooled), legacy, identifier + '/' + recipe['id'])
            self.assertEqual(codec.compact_pooled(pooled), pooled)
            self.assertEqual(codec.compact(pooled), pooled)
            self.assertEqual(codec.compact(legacy)['kind'], codec.COMPACT)
            self.assertEqual(digest(source), before)
            controls.append(source)
            expected.append({'pooled': digest(pooled), 'legacy': digest(legacy)})
        code = "const fs=require('node:fs'),crypto=require('node:crypto'),S=require('./finite-control-storage.js'),E=require('./local-experiment.js');E.run=E.verify=()=>{throw Error('No execution');};const hash=v=>crypto.createHash('sha256').update(E.stable(v)).digest('hex');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(c=>({pooled:hash(S.compactPooled(c)),legacy:hash(S.expand(S.compactPooled(c)))}))));"
        out = subprocess.run(['node', '-e', code], input=json.dumps(controls, ensure_ascii=True), cwd=ROOT, encoding='utf8', capture_output=True, check=True)
        self.assertEqual(json.loads(out.stdout), expected)

    def test_unicode_dictionary_and_literal_fallback_preserve_exact_text_and_detachment(self):
        for text in ['😀ᚠ\t\n"\\\x00' * 3, ''.join(chr(0x400 + i) for i in range(65)), '']:
            source = copy.deepcopy(self.single)
            source['members'][0]['control']['task']['pages'][0]['text'] = text
            pooled = codec.compact_pooled(source)
            self.assertEqual(codec.expand(pooled), source)
            if len(set(text)) > 64:
                self.assertEqual(pooled['textSymbols'], [])
                self.assertEqual(pooled['pools']['texts'][0], [0, text])
            restored = codec.expand(pooled)
            restored['members'][0]['control']['task']['alphabet'][0]['latin'] = 'CHANGED'
            self.assertEqual(codec.expand(pooled), source)
            source['members'][0]['control']['task']['pages'][0]['text'] = 'CHANGED'
            self.assertNotEqual(codec.expand(pooled), source)
        sibling = codec.expand(codec.compact_pooled(self.source))
        sibling['members'][0]['control']['task']['alphabet'][0]['latin'] = 'MUTATED'
        self.assertNotEqual(sibling['members'][1]['control']['task']['alphabet'][0]['latin'], 'MUTATED')

    def test_exact_fields_versions_typed_refs_tags_and_symbols_fail_closed(self):
        pooled = codec.compact_pooled(self.single)
        mutations = [lambda p: p.update(kind='finite-program-controls-pooled-v2'), lambda p: p.update(extra=True), lambda p: p['pools'].update(extra=[]), lambda p: p['rows'][0].append(0), lambda p: p['rows'][0].__setitem__(1, True), lambda p: p['rows'][0].__setitem__(1, -1), lambda p: p['rows'][0].__setitem__(1, len(p['pools']['strings'])), lambda p: p['rows'][0][5][0].__setitem__(1, True), lambda p: p['rows'][0][6].__setitem__(0, -1), lambda p: p['textSymbols'].append(p['textSymbols'][0]), lambda p: p['textSymbols'].__setitem__(0, 'ab'), lambda p: p['pools']['texts'][0].__setitem__(0, True), lambda p: p['pools']['texts'][0].__setitem__(1, '?'), lambda p: p['pools']['steps'][0].__setitem__(1, True), lambda p: p['rows'][0][0][0][2].__setitem__(0, 2)]
        for mutate in mutations:
            bad = copy.deepcopy(pooled)
            mutate(bad)
            with self.assertRaises(ValueError):
                codec.expand(bad)
            with self.assertRaises(ValueError):
                codec.compact_pooled(bad)
        bad = copy.deepcopy(pooled)
        bad['pools']['strings'].append('\ud800')
        with self.assertRaises(ValueError):
            codec.expand(bad)

    def test_unused_pools_and_ambiguous_literal_key_shapes_reject_in_both_codecs(self):
        bads = []
        for name, entry in [('strings', 'unused'), ('keys', [28]), ('texts', [0, 'unused']), ('steps', [{}, None])]:
            bad = codec.compact_pooled(self.single)
            bad['pools'][name].append(entry)
            bads.append(bad)
        bad = codec.compact_pooled(self.single)
        bad['pools']['steps'][0][0]['key'] = [1]
        bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):
                codec.expand(bad)
        code = "const fs=require('node:fs'),S=require('./finite-control-storage.js');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(c=>{try{S.expand(c);return false}catch{return true}})));"
        out = subprocess.run(['node', '-e', code], input=json.dumps(bads), cwd=ROOT, encoding='utf8', capture_output=True, check=True)
        self.assertEqual(json.loads(out.stdout), [True] * len(bads))

    def test_expansion_bombs_reject_before_decoding_or_repeated_key_copying(self):
        pooled = codec.compact_pooled(self.single)
        pooled['textSymbols'] = ['😀']
        pooled['pools']['texts'] = [[1, 'A' * 600000]]
        pooled['rows'][0][5][0][1] = 0
        with patch.object(codec._PackedText, 'decode', side_effect=AssertionError('decode before byte preflight')):
            with self.assertRaisesRegex(ValueError, 'byte bound'):
                codec.expand(pooled)
        pooled = codec.compact_pooled(self.single)
        pooled['rows'] = [copy.deepcopy(pooled['rows'][0]) for _ in range(1024)]
        pooled['pools']['keys'] = [[0] * 20000]
        pooled['pools']['steps'][0][1] = 0
        with patch.object(codec._PackedText, 'decode', side_effect=AssertionError('decode before node preflight')):
            with self.assertRaisesRegex(ValueError, 'structure bounds'):
                codec.expand(pooled)
        # Value-only node counting would fit; repeated object field names must
        # still obey the existing stricter Python legacy node budget.
        keyed = codec.compact_pooled(self.single)
        keyed['pools']['steps'] = [[{'literal_%d' % n: 0 for n in range(145)}, None]]
        keyed['rows'] = [copy.deepcopy(keyed['rows'][0]) for _ in range(1024)]
        with patch.object(codec._PackedText, 'decode', side_effect=AssertionError('decode before key-node preflight')):
            with self.assertRaisesRegex(ValueError, 'structure bounds'):
                codec.expand(keyed)
        pooled['rows'].append(copy.deepcopy(pooled['rows'][0]))
        with self.assertRaises(ValueError):
            codec.expand(pooled)

    def test_unsupported_legacy_fields_stay_lossless_and_inputs_are_plain_json(self):
        source = copy.deepcopy(self.single)
        source['members'][0]['control']['task']['extra'] = {'keep': 'literal'}
        self.assertEqual(codec.compact_pooled(source), source)
        class Unsafe(dict):
            pass
        with self.assertRaises(ValueError):
            codec.compact_pooled(Unsafe(source))
        source = codec.compact_pooled(self.single)
        source['rows'][0][0][0][2] = [0, float('inf')]
        with self.assertRaises(ValueError):
            codec.expand(source)


if __name__ == '__main__':
    unittest.main()
