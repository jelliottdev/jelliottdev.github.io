import unittest
from run_search_maximum_controls import nested,winner


class SelectionControls(unittest.TestCase):
    def test_ties_use_seed_not_enumeration_order(self):
        self.assertEqual(winner([{'seed':9,'score':-3},{'seed':2,'score':-3}])['seed'],2)

    def test_nested_maximum_and_true_key_count(self):
        candidates=[{'seed':i,'score':v,'matches_reference':False} for i,v in enumerate([-8,-6,-7,-6])]
        truth={'seed':100000,'score':-4,'matches_reference':True}
        rows=nested(candidates,[1,2,4],-5.5,truth)
        self.assertEqual([r['winner']['score'] for r in rows],[-8,-6,-6])
        self.assertEqual([r['winner']['seed'] for r in rows],[0,1,1])
        self.assertEqual([r['included_candidate_count'] for r in rows],[2,3,5])
        self.assertTrue(all(r['included_winner']==truth and r['included_score_accepted'] for r in rows))
        self.assertTrue(all(not r['score_accepted'] for r in rows))

    def test_true_key_need_not_win_a_tie(self):
        wrong={'seed':0,'score':-4,'matches_reference':False}
        truth={'seed':100000,'score':-4,'matches_reference':True}
        r=nested([wrong],[1],-5.5,truth)[0]
        self.assertFalse(r['included_winner']['matches_reference'])
        self.assertTrue(r['included_score_accepted'])


if __name__=='__main__':unittest.main()
