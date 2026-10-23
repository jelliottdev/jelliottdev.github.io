"""Independent scalar check of all token-role outputs and source byte arrays."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LATIN = ('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')
KEYWORDS = ('CICADA','3301','1033','DIVINITY','PRIMES','SACRED','LIBERPRIMUS',
            'INSTAR','EMERGENCE','ANEND','WISDOM','KOAN','MOBIUS','PARABLE',
            'THEPRIMESARESACRED','WELCOME','PILGRIM','TOTIENT')


def source_arrays():
    tree = ast.parse((HERE/'source/analysis/campaign7/a2_tokenpad.py').read_text(encoding='utf-8'))
    arrays = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ('P49','P50','P51'):
                arrays[name] = ast.literal_eval(node.value)
    assert [len(arrays[k]) for k in ('P49','P50','P51')] == [80,104,72]
    return bytes(arrays['P49'] + arrays['P50'] + arrays['P51'])


def corpus():
    source = (HERE/'source/data/krisyotam_runes.txt').read_text(encoding='utf-8')
    pages = [[RUNES.index(ch) for ch in part if ch in RUNES]
             for part in source.split('%') if any(ch in RUNES for ch in part)]
    assert len(pages) == 57
    for i, p in enumerate(pages):
        site_index = i if i < 50 else i+1
        site = json.loads((ROOT/f'data/pages/lp2-{site_index:02}.json').read_text(encoding='utf-8'))
        assert p == [RUNES.index(ch) for ch in site['raw'] if ch in RUNES]
    return pages


def model():
    counts = {}; total = 0
    for row in (HERE/'source/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        text, count = row.split(); count = int(count)
        counts[text] = count; total += count
    scale = math.log10(total)
    return {x:math.log10(n)-scale for x,n in counts.items()}, math.log10(.01)-scale


def score(text, weights, floor):
    text = ''.join(ch for ch in text.upper() if 'A' <= ch <= 'Z')
    return sum(weights.get(text[i:i+4],floor) for i in range(len(text)-3))/(len(text)-3)


def primes(n):
    values = []
    candidate = 2
    while len(values) < n:
        if all(candidate % q for q in values if q*q <= candidate):
            values.append(candidate)
        candidate += 1
    return values


def phi(n):
    out = 0
    for k in range(1,n+1):
        if math.gcd(k,n) == 1:out += 1
    return out


def schedules(n):
    prime = primes(n)
    fibonacci = []; a,b = 1,1
    for _ in range(n):fibonacci.append(a%256);a,b=b,a+b
    return {'prime':[x%256 for x in prime],
            'prime_minus_1':[(x-1)%256 for x in prime],
            'totient':[phi(i+2)%256 for i in range(n)],
            'fib':fibonacci}


def ratio(data):
    return sum(32 <= value <= 126 for value in data)/len(data)


def render_ascii(data):
    return ''.join(chr(v) if 32 <= v <= 126 else '.' for v in data)


def compare(expected, observed, tolerance=1e-10):
    assert abs(expected-observed) < tolerance, (expected, observed)


def check_cipher(data, result, weights, floor):
    parts = [data[:80],data[80:184],data[184:]]
    targets = [('p49',parts[0]),('p50',parts[1]),('p51',parts[2]),
               ('all',data),('all_rev',data[::-1])]
    groups = {'xor1':(-1,None),'xorkw':(-1,None),'additive':(-1,None),'as_is':(-1,None)}
    best = (-1,None)
    flagged = []
    count = 0

    def test(output, target, method, group):
        nonlocal count,best
        count += 1
        frac = ratio(output)
        rec = {'printable':frac,'target':target,'method':method,'preview':render_ascii(output)[:80]}
        if frac > groups[group][0]:groups[group] = (frac,rec)
        if frac > best[0]:best = (frac,rec)
        if frac > .85:flagged.append(score(render_ascii(output),weights,floor))

    for name,src in targets:
        n = len(src)
        for key in range(256):test([value ^ key for value in src],name,f'xor1 k={key}','xor1')
        for keyword in KEYWORDS:
            k = keyword.encode('ascii')
            test([value ^ k[i%len(k)] for i,value in enumerate(src)],name,f'xorkw {keyword}','xorkw')
        for stream_name,stream in schedules(n).items():
            for sign in (-1,1):
                test([(value+sign*stream[i])%256 for i,value in enumerate(src)],
                     name,f'{stream_name} sign{sign:+d}','additive')
        test(src,name,'asis','as_is')
    assert count == result['candidate_count'] == 1415
    assert best[1] == result['best']
    for group,(value,rec) in groups.items():
        compare(value,result['by_method'][group]['maximum_printable'])
        assert rec == result['by_method'][group]['winner']
    assert len(flagged) == result['flagged_over_0_85']
    if flagged:compare(max(flagged),result['best_flagged_quadgram'])
    else:assert result['best_flagged_quadgram'] is None


def check_index(data,pages,result,weights,floor):
    joined = [v for page in pages for v in page]
    outputs = {'idx_abs':[joined[b] for b in data if b<len(joined)],
               'self_gem':[b%29 for b in data]}
    position = 0;gap=[]
    for b in data:
        position = (position+b)%len(joined)
        gap.append(joined[position])
    outputs['idx_gaps'] = gap
    local = []
    for index,part in zip((49,50,51),(data[:80],data[80:184],data[184:])):
        local.extend(pages[index][b%len(pages[index])] for b in part)
    outputs['idx_page'] = local
    for name,values in outputs.items():
        rec = result[name]
        assert rec['rune_count'] == len(values)
        assert rec['rune_sha256'] == hashlib.sha256(bytes(values)).hexdigest()
        text = ''.join(LATIN[v] for v in values)
        assert rec['preview'] == text[:80]
        compare(rec['score'],score(text,weights,floor))


def check_controls(saved,pages,weights,floor):
    with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8',newline='') as f:
        known = [int(row['output_index']) for row in csv.DictReader(f)]
    joined = [r for pg in pages for r in pg]
    indexes = [joined[:256].index(r) for r in known]
    assert [joined[i] for i in indexes] == known
    assert [v%29 for v in known] == known
    compare(saved['known_quadgram'],score(''.join(LATIN[v] for v in known),weights,floor))
    assert saved['idx_abs_exact'] and saved['idx_gaps_exact'] and saved['self_gem_exact']
    assert 3 not in pages[49] and 3 in known
    assert saved['idx_page_known_unrepresentable_rune'] == 3
    phrase = ('THE PRIMES ARE SACRED. FOLLOW THE WHITE RABBIT. ' * 8)[:256]
    compare(saved['byte_plant_score'],score(phrase,weights,floor))
    assert saved['xor1_plant_exact'] and saved['additive_prime_plant_exact']
    assert saved['idx_page_legal_exact']


if __name__ == '__main__':
    saved = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert saved['plan_sha256'] == hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    pages = corpus();weights,floor = model()
    archived = source_arrays()
    assert archived == (HERE/'source-archived-256.bin').read_bytes()
    for name in ('archived','canon','resolved'):
        data = (HERE/f'source-{name}-256.bin').read_bytes();rec = saved['witnesses'][name]
        assert len(data) == 256 and rec['sha256'] == hashlib.sha256(data).hexdigest()
        assert rec['changed_cells_from_archived'] == [i for i in range(256) if data[i] != archived[i]]
        check_cipher(data,rec['ciphertext'],weights,floor)
        check_index(data,pages,rec['index'],weights,floor)
        print(f'PASS {name}: 1415 byte candidates and four index readings',flush=True)
    check_controls(saved['controls'],pages,weights,floor)
    original_cipher=json.loads((HERE/'source/analysis/campaign7/token_as_ciphertext_results.json').read_text(encoding='utf-8'))
    original_index=json.loads((HERE/'source/analysis/campaign7/token_as_index_results.json').read_text(encoding='utf-8'))
    assert round(saved['witnesses']['archived']['ciphertext']['best']['printable'],3) == original_cipher['best_printable_ratio']
    assert all(round(rec['score'],3) == original_index['scores'][name]
               for name,rec in saved['witnesses']['archived']['index'].items())
    print('PASS controls, source result parity and source/site rune mapping')
