"""Exhaustive small-alphabet and adversarial encoder/transition controls."""
import itertools
import unittest
from decoder_skip_controls import encode, transitions, true_path_failure, key_fixture,beam_decode,append_score


class Reject:
    def randrange(self,n):
        assert n==100
        return 0


class EncoderControls(unittest.TestCase):
    def test_small_alphabet_trace_and_transition(self):
        checked=0
        for plain in itertools.product(range(3),repeat=3):
            for key in itertools.product(range(3),repeat=5):
                p=list(plain); k=list(key)
                for mechanism in ('rigid','skip','rewrite','drift-skip'):
                    try:c,trace=encode(p,k,mechanism,modulus=3,draws=Reject())
                    except ValueError:continue
                    self.assertEqual(len(c),len(p))
                    for i,t in enumerate(trace):
                        # Invert the stored operations independently, including rewrites.
                        self.assertEqual((c[i]-int(t['rewritten'])-k[t['accepted_slot']])%3,p[i])
                        if i:
                            for slot in t['rejected_slots']:
                                self.assertEqual((p[i]+k[slot])%3,c[i-1])
                        else:self.assertEqual(t['rejected_slots'],[])
                    if mechanism in ('rigid','skip'):
                        self.assertIsNone(true_path_failure(c,p,trace,k,4,3))
                    if mechanism=='rigid':
                        self.assertEqual([(v-k[i])%3 for i,v in enumerate(c)],p)
                    checked+=1
        self.assertGreater(checked,20000)

    def test_transition_matches_enumerated_rejections(self):
        # Independently enumerate a candidate plaintext and its proposed rejected outputs.
        for key in itertools.product(range(3),repeat=4):
            for prior,cipher in itertools.product(range(3),repeat=2):
                expected=[]
                for slot in range(1,4):
                    for plain in range(3):
                        outputs=[(plain+key[k])%3 for k in range(1,slot+1)]
                        if outputs[-1]==cipher and outputs[:-1]==[prior]*(slot-1):
                            expected.append((slot,plain))
                self.assertEqual(transitions(cipher,prior,list(key),0,2,3),expected)

    def test_long_run_and_bound(self):
        p=[0,0]; k=[0,0,0,0,1]
        c,t=encode(p,k,'skip',modulus=3,draws=Reject())
        self.assertEqual(t[1]['rejected_slots'],[1,2,3])
        self.assertEqual(true_path_failure(c,p,t,k,2,3),1)
        self.assertIsNone(true_path_failure(c,p,t,k,3,3))

    def test_unrelated_advance_is_not_a_collision_skip(self):
        p=[0,0]; k=[0,1,2]
        c,t=encode(p,k,'drift-skip',modulus=3,draws=Reject())
        self.assertEqual(t[1]['unrelated_slots'],[1])
        self.assertEqual(true_path_failure(c,p,t,k,3,3),1)

    def test_correct_key_does_not_guarantee_unique_plaintext(self):
        key=[0,0,1]
        a,_=encode([0,1],key,'skip',modulus=3,draws=Reject())
        b,_=encode([0,0],key,'skip',modulus=3,draws=Reject())
        self.assertEqual(a,b)
        self.assertEqual(transitions(1,0,key,0,1,3),[(1,1),(2,0)])

    def test_rewrite_wraps_and_exhaustion_fails(self):
        c,t=encode([0,0],[2,2],'rewrite',modulus=3,draws=Reject())
        self.assertEqual(c,[2,0]);self.assertTrue(t[1]['rewritten'])
        with self.assertRaises(ValueError):encode([0,0],[0,0,0],'skip',modulus=3,draws=Reject())

    def test_repeated_key_fixture(self):
        base=key_fixture(0,slots=20)
        self.assertEqual(key_fixture(0,4,80),[v for v in base for _ in range(4)])
        self.assertNotEqual(base,key_fixture(1000,slots=20))

    def test_beam_against_exhaustive_paths(self):
        labels=['A','BB','C'];model={'ABBA':-1,'BBAB':-2,'CABB':-3};floor=-9
        key=[0,0,1,2,2,0,1,0,2,1,2,0,1]
        plain=[0,0,1,2,0]
        cipher,trace=encode(plain,key,'skip',modulus=3,draws=Reject())
        candidates=[]
        for advances in itertools.product(range(3),repeat=len(cipher)-1):
            slots=[0]
            for step in advances:slots.append(slots[-1]+1+step)
            if slots[-1]>=len(key):continue
            p=[(c-key[s])%3 for c,s in zip(cipher,slots)]
            if any((p[i]+key[j])%3!=cipher[i-1] for i in range(1,len(cipher)) for j in range(slots[i-1]+1,slots[i])):continue
            text=''.join(labels[v] for v in p)
            score=sum(model.get(text[i:i+4],floor) for i in range(len(text)-3))
            candidates.append((score,tuple(slots),tuple(p),text))
        expected=min(candidates,key=lambda v:(-v[0],v[1],v[2]))
        result=beam_decode(cipher,key,1000,2,labels,model,floor,plain,trace,3)
        self.assertEqual((result['cumulative_score'],tuple(result['slots']),tuple(result['indices']),result['transliteration']),expected)

    def test_structural_failure_and_pruning_are_separate(self):
        plain=[0,0];key=[0,0,1];c,t=encode(plain,key,'skip',modulus=3,draws=Reject())
        pruned=beam_decode(c,key,1,1,['A','B','C'],{},-9,plain,t,3)
        self.assertIsNone(pruned['first_invalid_truth_step'])
        self.assertEqual(pruned['first_pruned_truth_step'],1)
        invalid=beam_decode(c,key,1,0,['A','B','C'],{},-9,plain,t,3)
        self.assertEqual(invalid['first_invalid_truth_step'],1)
        self.assertIsNone(invalid['first_pruned_truth_step'])

    def test_incremental_scoring_with_multiletter_labels(self):
        model={'ABCD':-1,'BCDE':-2,'CDEF':-3};floor=-7
        for parts in [('A','BC','DEF'),('AB','CD','EF'),('ABCDEF',)]:
            text='';score=0
            for part in parts:score=append_score(score,text,part,model,floor);text+=part
            self.assertEqual(score,-6)


if __name__=='__main__':unittest.main()
