"""Independent source-domain checks; no manuscript decoding or source execution."""
import copy
import hashlib
import json
import shutil
import tempfile
import importlib.util
import subprocess
import unittest
from pathlib import Path
import build_repeating_key_banks as banks


def all_vectors(bank):
    result = []
    for start in range(0, bank['total'], 1024):
        result.extend(banks.resolve(dict(bankId=bank['id'], bankSha256=bank['sha256'], start=start, count=min(1024, bank['total'] - start))))
    return result


class RepeatingKeyBanksTest(unittest.TestCase):
    def test_complete_historical_schedule_census_and_exact_folded_partitions(self):
        data = banks.prepare()
        keys = [tuple(k) for k in data['banks'][0]['seeds']]
        complete, per_variant, by_variant = set(), {}, {}
        for variant in banks.VARIANTS:
            phased, named = set(), 0
            for key in keys:
                if variant == 'rotate-left':
                    whole = tuple(v for q in range(len(key)) for v in key[q:] + key[:q])
                elif variant == 'rotate-right':
                    whole = tuple(v for q in range(len(key)) for v in key[-q:] + key[:-q])
                elif variant == 'fold-repeat-endpoints':
                    whole = key + tuple(reversed(key))
                else:
                    whole = key + tuple(reversed(key[1:-1]))
                period = next(n for n in range(1, len(whole) + 1) if len(whole) % n == 0 and tuple(whole[i % n] for i in range(len(whole))) == whole)
                cycle = whole[:period]
                named += period
                phased.update(cycle[i:] + cycle[:i] for i in range(period))
            per_variant[variant] = named
            by_variant[variant] = sorted(phased)
            complete.update(phased)
        self.assertEqual(per_variant, dict(zip(banks.VARIANTS, [2561, 2561, 618, 532])))
        self.assertEqual(len(complete), 6272)
        self.assertEqual(sum(len(k) > 256 for k in complete), 648)
        self.assertEqual({len(k) for k in complete if len(k) > 256}, {324})
        for bank in data['banks'][2:]:
            expected = [list(k) for k in by_variant[bank['variant']]]
            actual = all_vectors(bank)
            self.assertEqual(actual, expected)
            if bank['variant'].startswith('fold-'):
                self.assertTrue(all(len(key) <= 36 for key in actual))
            else:
                self.assertEqual(len(actual), 2561)
                self.assertEqual(max(map(len, actual)), 324)
                self.assertEqual(sum(len(key) == 324 for key in actual), 324)
            self.assertEqual(bank['sourceAudit']['historicalSettings'], 6272)
            self.assertEqual(bank['historicalSettings'], per_variant[bank['variant']])
        self.assertEqual(data['banks'][0]['sha256'], '3fe9c14c22fc8f15649549ac5466781244064152b2cfb0b2b0fa3ddab69db54f')
        self.assertEqual(data['banks'][1]['sha256'], '0ee9bf1692106350b9bce71db7518b841f4389a13443f5b63b1f6215a6c3936a')

    def test_all_six_banks_match_frozen_engine_complete_schedules_and_node_chunks(self):
        data = banks.prepare()
        self.assertEqual(len(data['banks']), 6)
        spec = importlib.util.spec_from_file_location('frozen_schedule_engine', banks.ROOT / 'experiments/suites/classical-key-schedules/engine.py')
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        _, keys, _, _, _ = engine.load_inputs()
        historical = {variant: set() for variant in banks.VARIANTS}
        for variant, _, phase, _, _, cycle, _ in engine.configs('rotating-folded-key-openings', keys):
            historical[variant].add(cycle[phase:] + cycle[:phase])
        requests, expected = [], []
        for bank in data['banks']:
            actual = all_vectors(bank)
            if bank.get('variant'):
                self.assertEqual(actual, [list(k) for k in sorted(historical[bank['variant']])])
            for start in range(0, bank['total'], 1024):
                count = min(1024, bank['total'] - start)
                requests.append(dict(bankId=bank['id'], bankSha256=bank['sha256'], start=start, count=count))
                expected.append(hashlib.sha256(banks.stable(actual[start:start + count]).encode()).hexdigest())
        code = "const fs=require('node:fs'),crypto=require('node:crypto'),B=require('./repeating-key-banks.js');console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(ref=>crypto.createHash('sha256').update(JSON.stringify(B.resolve(ref))).digest('hex'))));"
        output = subprocess.run(['node', '-e', code], input=json.dumps(requests), cwd=banks.ROOT, text=True, encoding='utf8', capture_output=True, check=True)
        self.assertEqual(json.loads(output.stdout), expected)
        pins = {'public-wordlist-keys-v1': '3fe9c14c22fc8f15649549ac5466781244064152b2cfb0b2b0fa3ddab69db54f',
                'public-wordlist-rotations-v1': '0ee9bf1692106350b9bce71db7518b841f4389a13443f5b63b1f6215a6c3936a',
                'public-wordlist-fold-repeat-endpoints-v1': '536ba392b545cfb38edd4f26a5bec05cf08fc27492b5504e8442926a0b0d4afc',
                'public-wordlist-fold-skip-endpoints-v1': 'f9bebeb44886a52643c31e6c51e1a1f2230932eec2a5ffd47852b8173067946f'}
        self.assertEqual({b['id']: b['sha256'] for b in data['banks'] if b['id'] in pins}, pins)
        for bank in data['banks']:
            with self.assertRaises(ValueError):
                banks.resolve(dict(bankId=bank['id'], bankSha256=bank['sha256'], start=0, count=1025))

    def test_generated_files_are_current(self):
        for path, text in banks.files().items():
            self.assertEqual((banks.ROOT / path).read_bytes(), text.encode())

    def test_literal_source_domain_and_all_slices(self):
        data = banks.prepare()
        alphabet = json.loads((banks.ROOT / 'data/local-run-inputs.json').read_bytes())['alphabet']
        mapping = {r['rune']: i for i, r in enumerate(alphabet)}
        source = json.loads((banks.ROOT / 'experiments/records/public-wordlist-vigenere/plan.json').read_bytes())['keys']
        keys = [tuple(mapping[r] for r in k['runes']) for k in source]
        expected = [sorted(set(keys)), sorted({key[i:] + key[:i] for key in keys for i in range(len(key))})]
        self.assertEqual([len(v) for v in expected], [43, 309])
        for bank, vectors in zip(data['banks'], expected):
            self.assertEqual(hashlib.sha256(banks.stable({k: v for k, v in bank.items() if k != 'sha256'}).encode()).hexdigest(), bank['sha256'])
            for start in [0, 1, bank['total'] - 1]:
                count = min(17, bank['total'] - start)
                self.assertEqual(banks.resolve(dict(bankId=bank['id'], bankSha256=bank['sha256'], start=start, count=count)), [list(v) for v in vectors[start:start + count]])

    def test_descriptor_bounds_are_exact(self):
        bank = banks.prepare()['banks'][0]
        good = dict(bankId=bank['id'], bankSha256=bank['sha256'], start=0, count=1)
        for changes in [dict(count=0), dict(count=True), dict(start=False), dict(start=-1), dict(start=43), dict(start=42, count=2), dict(count=1025), dict(count=1.0), dict(bankSha256='0' * 64), dict(extra=True)]:
            with self.assertRaises(ValueError):
                banks.resolve({**good, **changes})
        actual = banks.resolve(good)
        actual[0].append(28)
        self.assertNotEqual(actual, banks.resolve(good))

    def test_every_pinned_source_is_required_and_cannot_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            names = [*banks.PINS, *banks.SCHEDULE_PINS, 'data/local-run-inputs.json']
            for name in names:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(banks.ROOT / name, root / name)
            self.assertEqual(banks.prepare(root), banks.prepare())
            for name in {**banks.PINS, **banks.SCHEDULE_PINS}:
                path = root / name
                original = path.read_bytes()
                path.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValueError, 'pin changed'):
                    banks.prepare(root)
                path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
