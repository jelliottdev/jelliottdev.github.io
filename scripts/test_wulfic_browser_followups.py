"""Source-derived prepared settings; synthetic controls only, no target decoding."""
import hashlib
import json
from pathlib import Path
import unittest

from browser_followups import WARNING12, validate_followups, runner

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'experiments/records/wulfic-autokey-seed-families'
SEED = [23, 18, 3, 4]
MODES = [(source, direction) for source in ('plaintext', 'ciphertext')
         for direction in ('subtract', 'add', 'beaufort')]


def source_decode(ciphertext, source, direction, seed):
    """Direct six recurrences from pinned p21_30_autokey_solver.py:150..228.

    Deliberately does not use constructor inverses, compiled runner operations,
    or the historical optimized engine's affine coefficient representation.
    """
    output = []
    for i, current in enumerate(ciphertext):
        key = (seed[i] if i < len(seed) else
               (output if source == 'plaintext' else ciphertext)[i - len(seed)])
        if direction == 'subtract':
            value = current - key
        elif direction == 'add':
            value = current + key
        elif direction == 'beaufort':
            value = key - current
        else:
            raise AssertionError('Unknown source mode')
        output.append(value % 29)
    return output


class WulficBrowserFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads((FOLDER / 'record.json').read_text(encoding='utf-8'))
        cls.recipes = cls.record['browser_followups']
        cls.deor = cls.recipes[:6]
        cls.word_reset = cls.recipes[6:]
        cls.inputs = json.loads((FOLDER / 'inputs.json').read_text(encoding='utf-8'))
        cls.plan = json.loads((FOLDER / 'plan.json').read_text(encoding='utf-8'))

    def test_exact_source_seed_and_pinned_provenance(self):
        self.assertEqual(self.inputs['source_commit'], 'bf89d3d13aad2b8f2c95ab195cf1b092f250775c')
        self.assertEqual(self.inputs['p21_distinct_keyword_vectors'], {'DEOR': SEED})
        self.assertEqual(self.inputs['p21_keywords']['DEOR'], SEED)
        self.assertEqual(self.inputs['comprehensive_keywords']['DEOR'], [23, 12, 4])
        self.assertNotEqual(self.inputs['comprehensive_keywords']['DEOR'], SEED)
        source = next(item for item in self.plan['source']['scripts']
                      if item['path'] == 'tools/legacy/p21_30_autokey_solver.py')
        self.assertEqual(source['git_blob'], 'c8ea084ed1f3abe175249587ae61c01bfb828331')

    def test_exact_complement_of_original_ten_page_domain(self):
        original = {Path(self.inputs['pages'][str(old)]['site_path']).stem
                    for old in range(21, 31)}
        self.assertEqual(original, {f'lp2-{n:02d}' for n in range(4, 14)})
        whole = {f'lp2-{n:02d}' for n in range(56) if n != 50}
        expected = sorted(whole - original)
        self.assertEqual(len(expected), 45)
        self.assertEqual(len(self.recipes), 8)
        self.assertEqual(len(self.deor), 6)
        for recipe in self.deor:
            self.assertEqual(recipe['card']['scope']['value'], {'pages': expected})
            self.assertEqual([p['id'] for p in recipe['inputs']['pages']], expected)
            self.assertFalse(original.intersection(recipe['card']['scope']['value']['pages']))
            for pin in recipe['inputs']['pages']:
                raw = json.loads((ROOT / 'data/pages' / (pin['id'] + '.json')).read_text(encoding='utf-8'))['raw']
                self.assertEqual(hashlib.sha256(raw.encode('utf-8')).hexdigest(), pin['text_sha256'])

    def test_all_six_programs_match_source_modes_including_beaufort_order(self):
        self.assertEqual([recipe['id'] for recipe in self.deor],
                         [f'deor-{source}-{direction}-warning' for source, direction in MODES])
        for recipe, (source, direction) in zip(self.deor, MODES):
            keyed = {'op': 'keyed-shift', 'key': SEED, 'mode': source + '-autokey',
                     'direction': direction if direction != 'beaufort' else
                     ('add' if source == 'plaintext' else 'subtract'), 'reset': 'page'}
            expected = [keyed]
            if direction == 'beaufort':
                affine = {'op': 'affine', 'a': 28, 'b': 0}
                expected = [affine, keyed] if source == 'plaintext' else [keyed, affine]
            self.assertEqual(recipe['control']['task']['steps'], expected)
            self.assertEqual(recipe['control']['task']['criterion'],
                             {'kind': 'exact-prefix', 'values': WARNING12})
            self.assertEqual(recipe['card']['rules']['reset'], {'status': 'specified', 'value': 'page'})
            self.assertEqual(recipe['inputs']['version'], 'raw')

    def test_complete_synthetic_warning_recovery_under_independent_source_recurrence(self):
        known = self.inputs['known_warning_gp']
        self.assertEqual(len(known), 184)
        self.assertEqual(known[:12], WARNING12)
        for recipe, (source, direction) in zip(self.deor, MODES):
            task = recipe['control']['task']
            runes = [entry['rune'] for entry in task['alphabet']]
            index = {rune: i for i, rune in enumerate(runes)}
            synthetic = task['pages'][0]['text']
            ciphertext = [index[ch] for ch in synthetic if ch in index]
            independent = source_decode(ciphertext, source, direction, SEED)
            self.assertEqual(independent, known, (source, direction))
            values = iter(independent)
            expected_text = ''.join(runes[next(values)] if ch in index else ch for ch in synthetic)
            result = runner.run(task)  # Synthetic fixture only; no manuscript task is run.
            self.assertEqual(result['transformed'][0]['text'], expected_text)
            self.assertEqual(result['matches'], [{'page': task['pages'][0]['id'], 'matched': True}])
            self.assertNotEqual(ciphertext, known)

    def test_shared_validator_accepts_all_authored_shapes_and_positive_controls(self):
        validate_followups(self.recipes, ROOT)

    def test_word_reset_scope_is_exact_feedback_eligible_four_page_subset(self):
        runes = {entry['rune'] for entry in self.word_reset[0]['control']['task']['alphabet']}

        def words(text):
            spans, position, start = [], 0, None
            for char in text + ' ':
                if char in runes:
                    if start is None:
                        start = position
                    position += 1
                elif start is not None:
                    spans.append((start, position - start))
                    start = None
            return spans

        eligible, first_feedback = [], {}
        for number in range(4, 38):
            page = f'lp2-{number:02d}'
            raw = json.loads((ROOT / 'data/pages' / (page + '.json')).read_text(encoding='utf-8'))['raw']
            positions = [start + 8 for start, length in words(raw) if length > 8 and start + 8 < 24]
            if positions:
                eligible.append(page)
                first_feedback[page] = min(positions)
        self.assertEqual(eligible, ['lp2-16', 'lp2-27', 'lp2-32', 'lp2-35'])
        self.assertEqual(first_feedback, {'lp2-16': 8, 'lp2-27': 11, 'lp2-32': 17, 'lp2-35': 15})
        # Precisely retain the partial-prefix overlap; W24 is not falsely called
        # wholly independent of FH3's repeating-key word reset.
        self.assertEqual([page for page, position in first_feedback.items() if position >= 12],
                         ['lp2-32', 'lp2-35'])
        for recipe in self.word_reset:
            self.assertEqual(recipe['card']['scope']['value'], {'pages': eligible})
            self.assertEqual(recipe['control']['task']['criterion'],
                             {'kind': 'exact-prefix', 'values': self.inputs['known_warning_gp'][:24]})

    def test_word_autokey_controls_enter_real_feedback_and_restart_after_long_word(self):
        seed = self.inputs['comprehensive_keywords']['DIVINITY']
        self.assertEqual(seed, [23, 10, 1, 10, 9, 10, 16, 26])
        self.assertEqual(len(self.word_reset), 2)
        for recipe, mode in zip(self.word_reset, ('plaintext', 'ciphertext')):
            task = recipe['control']['task']
            self.assertEqual(task['steps'], [{'op': 'keyed-shift', 'key': seed,
                                              'mode': mode + '-autokey', 'direction': 'subtract',
                                              'reset': 'word'}])
            runes = [entry['rune'] for entry in task['alphabet']]
            index = {rune: i for i, rune in enumerate(runes)}
            output, plain_word, cipher_word, keys, dynamic, reset_after = [], [], [], [], [], []
            used_feedback = False
            for char in task['pages'][0]['text']:
                if char not in index:
                    if used_feedback:
                        reset_after.append(len(output))
                    plain_word, cipher_word, used_feedback = [], [], False
                    continue
                current, position = index[char], len(cipher_word)
                if position < 8:
                    key = seed[position]
                else:
                    key = (plain_word if mode == 'plaintext' else cipher_word)[position - 8]
                    dynamic.append(len(output))
                    used_feedback = True
                plain = (current - key) % 29
                keys.append(key)
                output.append(plain)
                plain_word.append(plain)
                cipher_word.append(current)
            self.assertEqual(output, self.inputs['known_warning_gp'])
            self.assertEqual(dynamic, [139], 'Full control enters feedback in the nine-rune word')
            self.assertIn(140, reset_after)
            self.assertEqual(keys[140], seed[0], 'Next word restarts the seed after real feedback')
            expected_text_values = iter(output)
            expected_text = ''.join(runes[next(expected_text_values)] if ch in index else ch
                                    for ch in task['pages'][0]['text'])
            self.assertEqual(runner.run(task)['transformed'][0]['text'], expected_text)


if __name__ == '__main__':
    unittest.main()
