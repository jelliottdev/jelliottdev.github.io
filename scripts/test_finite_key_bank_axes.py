"""Independent Python finite-bank expansion against browser output; no decoding."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import finite_followup_cards as finite
import browser_followups as fixed
from build_repeating_key_banks import resolve
from test_finite_followup_cards import card, js

ROOT = Path(__file__).resolve().parents[1]
BANKS = json.loads((ROOT / 'data/repeating-key-banks.json').read_text(encoding='utf8'))['banks']


def axis(bank, start=1, count=4):
    return {'operation': 0, 'name': 'key', 'valuesFrom': {'bankId': bank['id'], 'bankSha256': bank['sha256'], 'start': start, 'count': count}}


def family(axes, pages=None):
    return card([{'id': 'repeating_key', 'direction': 'subtract', 'reset': 'page'}], axes, pages)


class BankAxes(unittest.TestCase):
    def test_literal_equivalence_browser_parity_and_detachment(self):
        for bank in BANKS:
            start = 1
            if bank['total'] > 1024:
                keys = resolve({'bankId': bank['id'], 'bankSha256': bank['sha256'], 'start': 0, 'count': 1024})
                start = next(n for n in range(len(keys) - 3) if all(len(k) <= 256 for k in keys[n:n + 4]))
            a = axis(bank, start, 4)
            compact = family([a])
            before = copy.deepcopy(compact)
            literal = family([{'operation': 0, 'name': 'key', 'values': resolve(a['valuesFrom'])}])
            expanded = finite.expand(compact)
            self.assertEqual(expanded, finite.expand(literal))
            browser = js([compact])[0]
            self.assertTrue(browser['ok'], browser)
            self.assertEqual(expanded, browser['value'])
            self.assertEqual(compact, before)
            expanded['variants'][0]['card']['method']['value']['operations'][0]['key'][0] = 28
            self.assertEqual(compact, before)
            self.assertNotEqual(expanded, finite.expand(compact))

    def test_ranges_and_exact_descriptor_boundaries(self):
        source = family([axis(BANKS[0])])
        for name, value in [('bankId', 'unknown'), ('bankSha256', '0' * 64), ('start', -1), ('start', True), ('start', .5), ('start', BANKS[0]['total']), ('count', 0), ('count', True), ('count', 1025), ('count', BANKS[0]['total'] + 1), ('extra', 1)]:
            bad = copy.deepcopy(source)
            bad['rules']['searchBounds']['value']['parameters'][0]['valuesFrom'][name] = value
            with self.assertRaises(ValueError):
                finite.expand(bad)
        for mutate in [lambda a: a.update(name='reset'), lambda a: a.update(values=[[0]]), lambda a: a.update(extra=True)]:
            bad = copy.deepcopy(source)
            mutate(bad['rules']['searchBounds']['value']['parameters'][0])
            with self.assertRaises(ValueError):
                finite.expand(bad)

    def test_full_pinned_count_and_cartesian_limits(self):
        for bank in BANKS:
            compact = family([axis(bank, 0, bank['total'])])
            if bank['total'] > 1024:
                with self.assertRaises(ValueError):
                    finite.expand(compact)
                self.assertFalse(js([compact])[0]['ok'])
                continue
            expanded = finite.expand(compact)
            self.assertEqual(expanded['declaration']['programCount'], bank['total'])
            self.assertEqual(expanded, js([compact])[0]['value'])
            bad = family([axis(bank, 0, bank['total']), {'operation': 0, 'name': 'unit', 'values': ['line', 'word', 'page']}, {'operation': 0, 'name': 'a', 'values': [0, 1]}])
            if bank['total'] * 6 > 1024:
                with self.assertRaisesRegex(ValueError, '1024'):
                    finite.expand(bad)

    def test_324_rune_bank_members_stay_literal_and_repeating_compiler_refuses_them(self):
        for bank in BANKS:
            if bank['total'] <= 1024:
                continue
            found, key = None, None
            for start in range(0, bank['total'], 1024):
                part = resolve({'bankId': bank['id'], 'bankSha256': bank['sha256'], 'start': start, 'count': min(1024, bank['total'] - start)})
                for n, value in enumerate(part):
                    if len(value) == 324:
                        found, key = start + n, value
                        break
                if found is not None:
                    break
            self.assertIsNotNone(found)
            self.assertEqual(finite.literal('key', key), key)
            compact = family([axis(bank, found, 1)])
            browser = js([compact])[0]
            self.assertTrue(browser['ok'])
            member = browser['value']['variants'][0]['card']
            self.assertEqual(member['method']['value']['operations'][0]['key'], key)
            self.assertEqual(len(key), 324)
            with self.assertRaises(ValueError):
                fixed.compile_card(member)
            with self.assertRaises(ValueError):
                finite.expand(compact)

    def test_expanded_byte_budget_is_not_bypassed_by_short_reference(self):
        keys = [[i % 29, (i // 29) % 29, i // 841] + [28] * 1497 for i in range(1024)]
        source = family([axis(BANKS[0], 0, 1024)])
        with patch('build_repeating_key_banks.resolve', return_value=keys):
            with self.assertRaisesRegex(ValueError, '8 MiB'):
                finite.expand(source)


if __name__ == '__main__':
    unittest.main()
