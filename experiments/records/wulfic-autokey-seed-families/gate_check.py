"""Test the original hit gate on a planted solved-reading-derived stream.

This checks detector power before any LP2 candidate score is examined.
"""
import ast
import json
import sys
from collections import Counter
from pathlib import Path

from engine import MODES, exhaustive

HERE=Path(__file__).resolve().parent
SOURCE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE.parents[3]/'source-archives/Wulfic-Cicada3301-Liber_Primus'
FUNCTIONS={'compute_ioc','check_singletons','test_seed',
           'autokey_pt_sub','autokey_pt_add','autokey_pt_beau',
           'autokey_ct_sub','autokey_ct_add','autokey_ct_beau'}


def source_functions():
    path=SOURCE/'tools/legacy/autokey_comprehensive.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS]
    assert len(selected)==len(FUNCTIONS)
    ns={'Counter':Counter}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),ns)
    return ns


def encipher(plain,seed,mode):
    out=[];lag=len(seed)
    for i,p in enumerate(plain):
        key=seed[i] if i<lag else (plain[i-lag] if mode.startswith('pt_') else out[i-lag])
        if mode.endswith('_sub'):c=(p+key)%29
        elif mode.endswith('_add'):c=(p-key)%29
        else:c=(key-p)%29
        out.append(c)
    return out


def main():
    data=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    row=data['pages']['21'];n=len(row['runes'])
    known=data['known_warning_gp']
    plain=[known[i%len(known)] for i in range(n)]
    for i,pos in enumerate(row['singletons']):plain[pos]=10 if i%2==0 else 24
    ns=source_functions()
    expected_ioc=ns['compute_ioc'](plain)
    assert expected_ioc>1.3
    seed=data['comprehensive_keywords']['CABAL']
    summaries=[]
    for mode in ('pt_sub','pt_add','pt_beau','ct_sub','ct_add','ct_beau'):
        cipher=encipher(plain,seed,mode)
        fn=ns['autokey_'+mode]
        assert fn(cipher,seed)==plain
        result=ns['test_seed'](cipher,[(pos,1) for pos in row['singletons']],seed,fn)
        assert result is not None
        ioc,passed,total,recovered=result
        assert ioc>1.3 and passed==total==len(row['singletons']) and recovered==plain
        wrong=[(value+1)%29 for value in seed]
        wrong_result=ns['test_seed'](cipher,[(pos,1) for pos in row['singletons']],wrong,fn)
        summaries.append({'mode':mode,'source_gate_pass':True,'planted_ioc':round(ioc,6),
                          'wrong_seed_gate_pass':wrong_result is not None and wrong_result[0]>1.3})
    # A ciphertext-feedback seed affects only its own prefix. The suffix is
    # invariant under every seed when the feedback lag is fixed.
    for mode in ('ct_sub','ct_add','ct_beau'):
        cipher=encipher(plain,seed,mode)
        base=ns['autokey_'+mode](cipher,seed)
        wrong=ns['autokey_'+mode](cipher,[(v+1)%29 for v in seed])
        assert base[len(seed):]==wrong[len(seed):]
    exhaustive_controls=[]
    for lag,seed in ((2,[7,13]),(3,[7,13,19])):
        for mode_index,mode in enumerate(MODES):
            cipher=encipher(plain,seed,mode)
            fn=ns['autokey_'+mode]
            source=ns['test_seed'](cipher,[(pos,1) for pos in row['singletons']],seed,fn)
            assert source is not None and source[0]>1.3
            search,_,_=exhaustive(cipher,row['singletons'],lag,mode_index)
            assert search['gate_count']>=1 and search['hit_count']>=1
            assert search['max_ioc']>=source[0]-1e-12
            exhaustive_controls.append({'lag':lag,'mode':mode,'source_gate_pass':True,
                                        'complete_search_has_hit':True,'gate_count':search['gate_count']})
    print(json.dumps({'page':row['page'],'planted_runes':n,'singletons':len(row['singletons']),
                      'known_reading_derived_ioc':round(expected_ioc,6),'modes':summaries,
                      'exhaustive_seed_controls':exhaustive_controls},indent=2))


if __name__=='__main__':main()
