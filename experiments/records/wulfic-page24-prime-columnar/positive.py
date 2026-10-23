"""Pre-outcome planted selector/transpose/shift and source-function controls."""
import ast
import hashlib
import json
import random
import subprocess
from pathlib import Path

from engine import columnar, inverse_columnar, ioc, primes_below, score, select, stage_two

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[3]/'source-archives/Wulfic-Cicada3301-Liber_Primus'
SCRIPT='tools/legacy/p24_prime0_post.py'
SOURCE_FUNCTIONS={'is_prime','compute_ioc','columnar_read','score_trigrams','indices_to_runeglish'}


def source_namespace(inputs):
    content=subprocess.check_output(['git','show',f"{inputs['source_commit']}:{SCRIPT}"],cwd=SOURCE)
    assert hashlib.sha256(content).hexdigest()==inputs['source_scripts'][SCRIPT]
    tree=ast.parse(content.decode('utf-8'))
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in SOURCE_FUNCTIONS]
    assert len(nodes)==len(SOURCE_FUNCTIONS)
    from collections import Counter
    ns={'Counter':Counter,'COMMON_3GRAMS':inputs['trigram_weights'],
        'IDX_TO_LETTER':['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S',
                         'T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA']}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),SCRIPT,'exec'),ns)
    return ns


def main():
    inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    n=len(inputs['runes']);weights=inputs['trigram_weights']
    ns=source_namespace(inputs)
    assert primes_below(n)==[i for i in range(n) if ns['is_prime'](i)]
    for width in (2,7,14):
        stream=list(range(46))
        assert columnar(stream,width)==ns['columnar_read'](stream,width)
        assert inverse_columnar(columnar(stream,width),width)==stream
    assert abs(ioc([1,1,2,3])-ns['compute_ioc']([1,1,2,3]))<1e-12
    for stream in ([16,8,18]*5,[0,10,28,23,2]*3):
        assert score(stream,weights)==ns['score_trigrams'](ns['indices_to_runeglish'](stream))
    rng=random.Random(3301)
    page=[rng.randrange(29) for _ in range(n)]
    locations=primes_below(n)
    desired=[(16,8,18)[i%3] for i in range(len(locations))]
    encrypted=[(value+5)%29 for value in desired]
    pre_columnar=inverse_columnar(encrypted,7)
    for position,value in zip(locations,pre_columnar):page[position]=value
    assert select(page,'prime0')==pre_columnar
    assert [(value-5)%29 for value in columnar(select(page,'prime0'),7)]==desired
    planted=stage_two(page,weights)
    assert planted[0]['trigram_score']>=score(desired,weights)
    null=[]
    for trial in range(49):
        trial_rng=random.Random(59103+trial)
        sample=[trial_rng.randrange(29) for _ in range(n)]
        null.append(stage_two(sample,weights)[0]['trigram_score'])
    assert planted[0]['trigram_score']>max(null)
    output={'schema':'liberpedia-wulfic-p24-positive-v1','planted_width':7,'planted_shift':5,
            'planted_runes':len(desired),'exact_extraction':True,
            'target_score':score(desired,weights),'full_search_best_score':planted[0]['trigram_score'],
            'uniform_control_count':len(null),'uniform_control_max':max(null),
            'source_function_parity':True}
    (HERE/'positive.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: exact source functions and planted prime/columnar/Caesar score above 49 synthetic controls')


if __name__=='__main__':main()
