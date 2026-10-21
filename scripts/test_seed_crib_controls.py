"""Boundary and exhaustive toy controls before running the frozen seed search."""
import itertools
import unittest
from seed_crib_controls import accepted, digest_input

class Controls(unittest.TestCase):
    def test_rejection_and_byte_order(self):
        self.assertEqual(accepted(bytes([0,28,29,231,232,255])),[0,28,0,28])
        self.assertEqual(digest_input(0x01020304,0x05060708),
            b'liberpedia-seed-control:v1:\x01\x02\x03\x04\x05\x06\x07\x08')
        self.assertEqual(digest_input(0,0)[-8:],bytes(8))
        with self.assertRaises(OverflowError):digest_input(-1,0)
        with self.assertRaises(OverflowError):digest_input(0,2**32)

    def test_all_two_symbol_modular_controls(self):
        words=list(itertools.product(range(3),repeat=2))
        for plain,key in itertools.product(words,repeat=2):
            cipher=tuple((a+b)%3 for a,b in zip(plain,key))
            correct=[];wrong=[]
            for candidate in words:
                decoded=tuple((a-b)%3 for a,b in zip(cipher,candidate))
                if decoded[0]==plain[0]:correct.append(decoded)
                if decoded[0]==(plain[0]+1)%3:wrong.append(decoded)
            self.assertEqual(len(correct),3)
            self.assertEqual(sum(p==plain for p in correct),1)
            self.assertEqual(sum(p[1]==plain[1] for p in correct),1)
            self.assertEqual(len(wrong),3)
            self.assertTrue(all(p!=plain for p in wrong))
            self.assertEqual(sum(p[1]==plain[1] for p in wrong),1)

if __name__=='__main__':unittest.main()
