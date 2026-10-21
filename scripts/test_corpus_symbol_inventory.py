"""Boundary controls for the historical prefix symbol inventory."""
import unittest
from corpus_symbol_inventory import measure
from check_corpus_symbol_inventory import scan
from itertools import product

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

    def test_independent_scanner_exhaustive_small_inputs(self):
        for size in range(6):
            for chars in product(['ᚠ','ᛂ',' ','\n'],repeat=size):
                raw=''.join(chars).encode()
                result=measure(raw,{'ᚠ'})
                checked,lengths=scan(raw,{'ᚠ'})
                self.assertEqual(checked,{k:v for k,v in result.items() if k not in ['bytes','sha256']})
                self.assertEqual(sum(int(k)*n for k,n in lengths.items()),result['counted_units'])
        raw=('ᚠ '*2902+'ᛂ').encode()
        self.assertEqual(scan(raw,{'ᚠ'})[0]['outside_alphabet'],{})
        with self.assertRaises(UnicodeDecodeError):scan(b'\xff',{'ᚠ'})

if __name__=='__main__':unittest.main()
