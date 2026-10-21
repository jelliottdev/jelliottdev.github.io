"""Boundary controls for the historical prefix symbol inventory."""
import unittest
from corpus_symbol_inventory import measure

class PrefixInventory(unittest.TestCase):
    def test_literal_spaces_and_newline(self):
        result=measure('  ᚠᛂ  ᚠ\nᚠ '.encode(),{'ᚠ'})
        self.assertEqual(result['selected_tokens'],2)
        self.assertFalse(result['eligible'])
        self.assertEqual(result['outside_alphabet'],{'\n':1,'ᛂ':1})
        self.assertEqual(result['tokens_with_outside_symbols'],2)
        self.assertEqual(result['counted_units'],5)

    def test_prefix_boundary(self):
        result=measure(('ᚠ '*2902+'ᛂ').encode(),{'ᚠ'})
        self.assertTrue(result['eligible'])
        self.assertEqual(result['selected_tokens'],2902)
        self.assertEqual(result['outside_alphabet'],{})
        self.assertEqual(result['symbols'],{'ᚠ':2902})

    def test_empty_and_strict_decoding(self):
        self.assertEqual(measure(b'   ',{'ᚠ'})['selected_tokens'],0)
        with self.assertRaises(UnicodeDecodeError):measure(b'\xff',{'ᚠ'})

if __name__=='__main__':unittest.main()
