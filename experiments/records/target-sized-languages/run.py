"""Recompute the exact-token language control and compare with saved evidence."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from run_target_sized_languages import produce
if __name__=='__main__':
    assert produce()==json.loads((Path(__file__).parent/'results.json').read_bytes())
    print('Reproduced all 177 exact-token profiles and comparisons.')
