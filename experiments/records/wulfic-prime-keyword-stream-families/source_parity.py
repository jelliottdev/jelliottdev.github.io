"""Compare selected engine operations with functions extracted from pinned upstream.

Requires a local checkout of Wulfic/Cicada3301-Liber_Primus at the plan commit.
No original source code is copied into the public experiment bundle.
"""
import ast
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from engine import GP_PRIMES, MODES, STEPPED_VARIANTS, decode, fskip_decode, key_matrix, normalized_ioc, repeated
from engine import first_primes, prime_key, prime_orderings, quick_score

HERE = Path(__file__).resolve().parent
SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parents[3] / 'source-archives/Wulfic-Cicada3301-Liber_Primus'
COMMIT = 'bf89d3d13aad2b8f2c95ab195cf1b092f250775c'


def extracted(path, function_names, namespace):
    text = path.read_text(encoding='utf-8')
    tree = ast.parse(text)
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in function_names]
    assert len(selected) == len(function_names), (path, [x.name for x in selected])
    code = compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec')
    exec(code, namespace)
    return namespace


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() == COMMIT
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    for item in plan['source']['scripts']:
        blob = subprocess.check_output(['git','rev-parse',f'HEAD:{item["path"]}'], cwd=SOURCE, text=True).strip()
        assert blob == item['git_blob'], item['path']
    data = json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    legacy = SOURCE/'tools/legacy'
    script = legacy/'keyword_stepped_stream.py'
    ns = {'PRIMES': first_primes(10000).tolist()}
    ns['TOTIENT_MOD29'] = [(p-1)%29 for p in ns['PRIMES']]
    extracted(script, {'generate_keyword_stepped_stream'}, ns)
    names, matrix, _ = key_matrix(data['stepped_keywords'], max(len(x['runes']) for x in data['pages'].values()))
    for word in ('CABAL', 'AETHEREAL', 'DIVINITY'):
        wi = names.index(word)
        for variant in STEPPED_VARIANTS:
            vi = STEPPED_VARIANTS.index(variant)
            for offset in (0, 47, 1000):
                for length in (1, 37, 261):
                    row = (wi*8+vi)*1001+offset
                    expected = ns['generate_keyword_stepped_stream'](data['stepped_keywords'][word], length, offset, variant)
                    assert expected is not None
                    assert matrix[row, :length].tolist() == expected, (word, variant, offset, length)

    ns_kw = {'N':29, 'Counter':Counter}
    source_kw = legacy/'p21_30_keyword_sweep.py'
    tree = ast.parse(source_kw.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('DIGRAPHS','SINGLES_MAP') for t in node.targets):
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(source_kw), 'exec'), ns_kw)
    extracted(source_kw, {'parse_keyword','decrypt','ioc'}, ns_kw)
    for word, values in data['keyword_only'].items():
        assert ns_kw['parse_keyword'](word) == values
    cipher = data['pages']['21']['runes']
    for word in ('CABAL','AETHEREAL'):
        key = data['keyword_only'][word]
        for mode in MODES:
            expected = ns_kw['decrypt'](cipher,key,mode)
            actual = decode(cipher,repeated(key,len(cipher)),mode)
            assert actual.tolist() == expected
            assert abs(normalized_ioc(actual)-ns_kw['ioc'](expected)) < 1e-12

    ns_pr = {'Counter':Counter, 'ALL_PRIMES':first_primes(5133).tolist()}
    ns_pr['PRIME_SET'] = set(ns_pr['ALL_PRIMES'])
    ns_pr['GP_PRIMES'] = GP_PRIMES
    source_pr = legacy/'prime_stream_solver.py'
    extracted(source_pr, {'sequential_primes','fibonacci_indexed_primes','spiral_ordered_primes','telnet_gap_primes',
                          'gp_primes_extended','reversed_gp_primes','ks_totient','ks_prime_mod29',
                          'ks_prime_index_mod29'}, ns_pr)
    rows, all_primes = prime_orderings(131)
    lookup = dict(rows)
    comparisons = [('seq_off40','sequential_primes',(40,131)),('fib_idx','fibonacci_indexed_primes',(131,)),
                   ('spiral','spiral_ordered_primes',(131,)),('gap','telnet_gap_primes',(131,)),
                   ('gp_ext','gp_primes_extended',(131,)),('rev_gp','reversed_gp_primes',(131,))]
    for label, func, args in comparisons:
        assert list(lookup[label]) == ns_pr[func](*args), label
    for label in ('seq_off0','fib_idx','spiral','gap','rev_gp'):
        values = lookup[label]
        for kind, func in [('totient','ks_totient'),('p_mod29','ks_prime_mod29'),('idx_mod29','ks_prime_index_mod29')]:
            assert prime_key(values,kind,all_primes).tolist() == ns_pr[func](list(values)), (label,kind)
    print('PASS: pinned source key generators, 8 stepped variants, keyword parsing and decoders')


if __name__ == '__main__': main()
