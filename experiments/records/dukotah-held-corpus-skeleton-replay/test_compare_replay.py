"""Offline comparison tests on copied JSON objects, never a target rerun."""
import sys,copy,json,unittest
from pathlib import Path
sys.dont_write_bytecode=True
from compare_replay import differences,compare
H=Path(__file__).resolve().parent
class Comparison(unittest.TestCase):
    def test_saved_files(self):self.assertEqual(compare(H/'reproduction/positive_control_T0.json',H/'reproduction/scan_results.json'),[])
    def test_small_float_roundoff(self):self.assertEqual(differences({'count':593.00001},{'count':592.99999}),[])
    def test_changed_score(self):self.assertTrue(differences({'count':593.0},{'count':594.0}))
    def test_changed_offset_is_not_silently_treated_as_tie(self):self.assertTrue(differences({'offset':145429},{'offset':145430}))
    def test_missing_pattern(self):
        a=json.loads((H/'reproduction/scan_results.json').read_text());b=copy.deepcopy(a);del b['best']['real:interval'];self.assertTrue(differences(a,b))
    def test_changed_plant_truth(self):
        a=json.loads((H/'reproduction/positive_control_T0.json').read_text());b=copy.deepcopy(a);b['results'][0]['truth']['offset']+=1;self.assertTrue(differences(a,b))
    def test_nonfinite_and_wrong_types(self):
        for value in [float('nan'),float('inf'),'593',True]:self.assertTrue(differences(593.0,value))
if __name__=='__main__':unittest.main()
