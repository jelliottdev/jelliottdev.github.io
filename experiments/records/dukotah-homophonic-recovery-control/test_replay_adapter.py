"""Check the deterministic comparison boundary without rerunning controls."""
import copy
import unittest

from replay_controls import deterministic, first_difference


class ReplayComparisonTests(unittest.TestCase):
    def test_only_declared_timing_positions_are_ignored(self):
        before = {'seconds': 1.0, 'benchmark': [0.1, 0.2], 'projected_seconds': 40,
                  'cases': [{'fit': {'seconds': 2.0, 'returned_score': -3.0},
                             'heldout': {'seconds': 7.0, 'z': 1.0}}]}
        after = copy.deepcopy(before)
        after.update(seconds=99.0, benchmark=[9.0, 8.0], projected_seconds=400)
        after['cases'][0]['fit']['seconds'] = 100.0
        self.assertIsNone(first_difference(deterministic(before), deterministic(after)))
        after['cases'][0]['heldout']['seconds'] = 8.0
        self.assertIsNotNone(first_difference(deterministic(before), deterministic(after)))

    def test_scores_maps_and_decisions_are_not_ignored(self):
        baseline = {'cases': [{'fit': {'returned_score': -3.0, 'returned_psi': [0, 1, 2]},
                               'source_partc': {'strict_z_above_3': False, 'z': 1.0}}]}
        for field, value in [('returned_score', -3.0 + 1e-12), ('returned_psi', [0, 2, 1])]:
            changed = copy.deepcopy(baseline)
            changed['cases'][0]['fit'][field] = value
            self.assertIsNotNone(first_difference(deterministic(baseline), deterministic(changed)))
        changed = copy.deepcopy(baseline)
        changed['cases'][0]['source_partc']['strict_z_above_3'] = True
        self.assertIsNotNone(first_difference(deterministic(baseline), deterministic(changed)))

    def test_json_types_keys_and_order_are_exact(self):
        for left, right in [(False, 0), (1, 1.0), ([0, 1], [1, 0]), ({'a': 1}, {'a': 1, 'b': 2})]:
            self.assertIsNotNone(first_difference(left, right))


if __name__ == '__main__':
    unittest.main()
