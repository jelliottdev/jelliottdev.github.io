"""Independent source-domain checks; no manuscript decoding or source execution."""
import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import build_repeating_key_banks as banks


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
            actual = banks.resolve(dict(bankId=bank['id'], bankSha256=bank['sha256'], start=0, count=bank['total']))
            self.assertEqual(actual, expected)
            self.assertTrue(all(len(key) <= 36 for key in actual))
            self.assertEqual(bank['sourceAudit']['historicalSettings'], 6272)
            self.assertEqual(bank['historicalSettings'], per_variant[bank['variant']])
        self.assertEqual(data['banks'][0]['sha256'], '3fe9c14c22fc8f15649549ac5466781244064152b2cfb0b2b0fa3ddab69db54f')
        self.assertEqual(data['banks'][1]['sha256'], '0ee9bf1692106350b9bce71db7518b841f4389a13443f5b63b1f6215a6c3936a')

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
