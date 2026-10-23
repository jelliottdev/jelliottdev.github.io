"""Sample and exhaustive-small-grid parity with pinned source functions."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from engine import MODES, coefficients, decode_affine, exhaustive, named
from gate_check import SOURCE, source_functions

HERE=Path(__file__).resolve().parent


def main():
    data=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip()==plan['source']['commit']
    for item in plan['source']['scripts']:
        assert subprocess.check_output(['git','rev-parse',f'HEAD:{item["path"]}'],cwd=SOURCE,text=True).strip()==item['git_blob']
    ns=source_functions()
    for page in ('21','25','31','39','54'):
        row=data['pages'][page]
        cipher=row['runes'];singletons=[(pos,1) for pos in row['singletons']]
        for mi,mode in enumerate(MODES):
            source=ns['autokey_'+mode]
            for seed in ([0,0],[7,13,19],data['comprehensive_keywords']['CABAL'],data['comprehensive_keywords']['DEOR']):
                a,b=coefficients(np.asarray(cipher,dtype=np.int64),len(seed),mi)
                actual=decode_affine(a,b,np.asarray(seed,dtype=np.int64)).tolist()
                expected=source(cipher,seed)
                assert actual==expected,(page,mode,seed)
                source_gate=ns['test_seed'](cipher,singletons,seed,source)
                own_score,_,_=named(cipher,row['singletons'],seed,mi)
                assert (own_score is None)==(source_gate is None)
                if source_gate is not None:assert abs(own_score-source_gate[0])<1e-12
    for page,mode in (('21',0),('31',3)):
        row=data['pages'][page];cipher=row['runes'];singles=[(pos,1) for pos in row['singletons']]
        own,_,_=exhaustive(cipher,row['singletons'],2,mode)
        passed=0;hits=0;max_ioc=-1
        for a in range(29):
            for b in range(29):
                source=ns['test_seed'](cipher,singles,[a,b],ns['autokey_'+MODES[mode]])
                if source is not None:
                    passed+=1;hits+=source[0]>1.3;max_ioc=max(max_ioc,source[0])
        assert (passed,hits)==(own['gate_count'],own['hit_count'])
        if passed:assert abs(max_ioc-own['max_ioc'])<1e-12
    print('PASS: pinned source blobs, 120 sample decodes/gates and two complete 841-seed parity grids')


if __name__=='__main__':main()
