"""Aligned FLORES comparison. Standard library, offline; --check verifies saved outputs.

All scoring choices are in the committed plan. No fitted classifier or language posterior.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import random
import unicodedata as ud

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODES = ('letters', 'folded', 'gp-length')
GP = ('ing', 'th', 'eo', 'ng', 'oe', 'ae', 'ia', 'io', 'ea')
WELSH = ('ch', 'dd', 'ff', 'ng', 'll', 'ph', 'rh', 'th')


def tokenize(text, mode):
    text = ud.normalize('NFC', text.lower())
    if mode in ('folded', 'gp-length'):
        text = ''.join(c for c in ud.normalize('NFD', text) if not ud.category(c).startswith('M'))
    words = []; current = ''
    for i, c in enumerate(text):
        if c.isalpha():
            current += c
        elif c in "'\u2019" and current and i + 1 < len(text) and text[i+1].isalpha():
            continue
        elif current:
            words.append(current); current = ''
    if current: words.append(current)
    groups = GP if mode == 'gp-length' else WELSH if mode == 'welsh-digraph' else ()
    result = []
    for word in words:
        units = []; i = 0
        while i < len(word):
            unit = next((g for g in groups if word.startswith(g, i)), word[i])
            i += len(unit)
            if mode == 'gp-length':
                unit = {'ing':'ng', 'io':'ia', 'k':'c', 'z':'s'}.get(unit, unit)
            units.append(unit)
        result.append(units)
    return result


def stats(words):
    lengths = Counter(min(len(w), 16) for w in words)
    counts = Counter(c for w in words for c in w)
    n = sum(counts.values()); pairs = sum(len(w)-1 for w in words)
    equal = sum(a == b for w in words for a, b in zip(w, w[1:]))
    return dict(tokens=len(words), units=n, distinct=len(counts),
                histogram=[lengths[i] for i in range(1,17)],
                ioc=sum(v*(v-1) for v in counts.values())/(n*(n-1)),
                adjacent_equal=equal/pairs, adjacent_pairs=pairs, equal_pairs=equal,
                symbol_counts=dict(sorted(counts.items())))


def tv(a,b):
    return sum(abs(x/sum(a)-y/sum(b)) for x,y in zip(a,b))/2


def quantile(values, q):
    v=sorted(values); x=(len(v)-1)*q; i=int(x)
    return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)


def calculate():
    plan=json.loads((HERE/'plan.json').read_bytes())
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'], item['path']
    ledger=json.loads((ROOT/'exports/unsolved-word-tokens.json').read_bytes())
    target=stats([[c for c in t['token'] if c != "'"] for t in ledger])
    assert target['tokens']==2896 and target['units']==12956
    rows={split:list(csv.DictReader((HERE/f'metadata_{split}.tsv').open(encoding='utf-8'),delimiter='\t')) for split in ('dev','devtest')}
    corpus={split:{code:(HERE/f'{code}.{split}.txt').read_text(encoding='utf-8').splitlines() for code in plan['languages']} for split in rows}
    for split in rows:
        assert all(len(lines)==len(rows[split]) for lines in corpus[split].values())
    groups=defaultdict(list)
    for i,row in enumerate(rows['devtest']): groups[row['URL']].append(i)
    keys=sorted(groups); rng=random.Random(3301)
    draws=[[rng.choice(keys) for _ in keys] for _ in range(200)]
    report={'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'target':target, 'sentence_counts':{s:len(r) for s,r in rows.items()},
            'bootstrap_article_clusters':len(keys), 'modes':{}}
    for mode in MODES:
        profiles={s:{} for s in rows}; clusters={}
        for code in plan['languages']:
            for split in rows:
                sentences=[tokenize(line,mode) for line in corpus[split][code]]
                profiles[split][code]=stats([w for sentence in sentences for w in sentence])
                if split=='devtest':
                    clusters[code]={key:Counter(min(len(w),16) for i in ids for w in sentences[i]) for key,ids in groups.items()}
        distances={c:[] for c in plan['languages']}; wins=Counter()
        for draw in draws:
            ds={}
            for code in plan['languages']:
                h=Counter()
                for key in draw: h.update(clusters[code][key])
                ds[code]=tv(target['histogram'],[h[i] for i in range(1,17)])
                distances[code].append(ds[code])
            best=min(ds.values())
            for code,d in ds.items():
                if abs(d-best)<1e-12: wins[code]+=1
        ranking=[]
        for code in plan['languages']:
            st=profiles['devtest'][code]
            ranking.append({'code':code,'language':plan['languages'][code],**st,
                'length_tv':tv(target['histogram'],st['histogram']),
                'ioc_distance':abs(st['ioc']-target['ioc']),
                'adjacent_distance':abs(st['adjacent_equal']-target['adjacent_equal']),
                'bootstrap_tv_95_percentile':[quantile(distances[code],.025),quantile(distances[code],.975)],
                'bootstrap_best_count':wins[code]})
        ranking.sort(key=lambda x:x['length_tv'])
        controls=[]
        for code in plan['languages']:
            scores=sorted((tv(profiles['devtest'][code]['histogram'],st['histogram']),c) for c,st in profiles['dev'].items())
            controls.append({'actual':code,'nearest':scores[0][1],'all_distances':scores})
        report['modes'][mode]={'ranking':ranking,'held_out_controls':controls,
            'correct_controls':sum(x['actual']==x['nearest'] for x in controls)}
    st=stats([w for line in corpus['devtest']['cym_Latn'] for w in tokenize(line,'welsh-digraph')])
    report['welsh_digraph_sensitivity']={**st,'length_tv':tv(target['histogram'],st['histogram'])}
    return report


def figure(report):
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="700" viewBox="0 0 360 700" role="img" aria-labelledby="t d">',
         '<title id="t">Language similarity depends on the counting model</title>',
         '<desc id="d">Word-length total variation distance, lower is closer. Eight languages from aligned FLORES devtest sentences. Bars show full-corpus scores, lines show article-bootstrap percentile ranges. Not probabilities of plaintext language.</desc>',
         '<rect width="360" height="700" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#263b45">',
         '<text x="16" y="27" font-size="19">Word-length comparison</text>',
         '<text x="16" y="49" font-size="13">Lower is closer; not a decryption</text>']
    for k,mode in enumerate(('letters','gp-length')):
        top=84+k*288
        out.append(f'<text x="16" y="{top}" font-size="16">{("Letters with accents", "GP grouping sensitivity")[k]}</text>')
        for i,row in enumerate(report['modes'][mode]['ranking']):
            y=top+25+i*29; lo,hi=row['bootstrap_tv_95_percentile']; scale=450
            out += [f'<text x="16" y="{y+4}" font-size="14">{row["language"]}</text>',
                    f'<rect x="95" y="{y-9}" width="{row["length_tv"]*scale:.2f}" height="16" fill="{("#99642d" if row["language"]=="Welsh" else "#315f73")}"/>',
                    f'<path d="M{95+lo*scale:.2f} {y-1}H{95+hi*scale:.2f}" stroke="#111" stroke-width="2"/>',
                    f'<text x="305" y="{y+4}" font-size="14">{row["length_tv"]:.3f}</text>']
    out += ['<text x="16" y="661" font-size="13">Lines: 200 paired article resamples.</text>',
            '<text x="16" y="682" font-size="13">Interpretation depends on cipher and corpus.</text></g></svg>']
    return '\n'.join(out)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    report=calculate()
    outputs={'results.json':json.dumps(report,ensure_ascii=False,indent=2)+'\n','comparison.svg':figure(report)}
    for name,text in outputs.items():
        if args.check: assert (HERE/name).read_text(encoding='utf-8')==text,name
        else: (HERE/name).write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({m:{'ranking':[(x['language'],round(x['length_tv'],4),x['bootstrap_best_count']) for x in r['ranking']], 'correct_controls':r['correct_controls']} for m,r in report['modes'].items()},indent=2))


if __name__=='__main__': main()
