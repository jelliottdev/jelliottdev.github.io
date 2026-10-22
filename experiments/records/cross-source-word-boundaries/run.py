"""Measure word-token sensitivity to two preserved LP2 transcriptions."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
RUNE=re.compile(r'[\u16a0-\u16ff]')


def sha(data):return hashlib.sha256(data).hexdigest()


def source_pages():
    raw=(ROOT/'exports/sources/cicada-2014-seventh-onion/0-55.jpg.runes.txt').read_text(encoding='utf-8')
    blocks=re.split(r'(?m)^%\s*$',raw)
    assert len(blocks)==56
    return [block.strip('\r\n') for block in blocks]


def joined(parts):
    return ''.join(part.translate(str.maketrans('','','/\r\n')) for part in parts)


def tokenize(parts,alphabet):
    chars=joined(parts)
    pattern=re.compile('['+''.join(sorted(alphabet))+"]+(?:'['"+''.join(sorted(alphabet))+']+)*')
    prefix=[0]
    for char in chars:prefix.append(prefix[-1]+(char in alphabet))
    found=[]
    for match in pattern.finditer(chars):
        found.append((prefix[match.start()],sum(c in alphabet for c in match.group())))
    starts=[entry[0] for entry in found]
    lengths=[entry[1] for entry in found]
    histogram=Counter(lengths)
    return {'runes':prefix[-1],'tokens':len(found),'starts':starts,
            'histogram':{str(k):histogram[k] for k in sorted(histogram)},
            'long_tokens_10_plus':sum(n>=10 for n in lengths),
            'eleven_eleven_ten_windows':sum(lengths[i:i+3]==[11,11,10] for i in range(len(lengths)-2))}


def assemble(gaps,runes):
    return ''.join(gap+rune for gap,rune in zip(gaps,runes))+gaps[-1]


def metrics(result):
    return {key:value for key,value in result.items() if key!='starts'}


def report():
    plan_bytes=(HERE/'plan.json').read_bytes();plan=json.loads(plan_bytes)
    for item in plan['inputs']:
        assert sha((ROOT/item['path']).read_bytes())==item['sha256'],item['path']
    alphabet={entry['rune'] for entry in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
    archived=source_pages()
    wiki=[(ROOT/f'text/lp2-{n:02d}.txt').read_text(encoding='utf-8').strip('\r\n') for n in range(56)]
    sections=[];differences=[];rune_base=0
    for n,(old,new) in enumerate(zip(archived,wiki)):
        old_runes=RUNE.findall(old);new_runes=RUNE.findall(new)
        assert old_runes==new_runes and set(old_runes)<=alphabet
        old_gaps=RUNE.split(old);new_gaps=RUNE.split(new)
        for local,(a,b) in enumerate(zip(old_gaps,new_gaps)):
            if a!=b:
                differences.append({'page':f'lp2-{n:02d}','page_number':n,'before_page_rune_ordinal':local,
                                    'before_global_rune_ordinal':rune_base+local,
                                    'source_gap':a,'wiki_gap':b})
        sections.append({'runes':new_runes,'gaps':new_gaps})
        rune_base+=len(new_runes)
    assert len(differences)==33 and rune_base==12956
    wiki_result=tokenize(wiki,alphabet)
    source_result=tokenize(archived,alphabet)
    assert wiki_result['runes']==source_result['runes']==12956
    baseline_starts=set(wiki_result['starts'])
    rows=[]
    for change in differences:
        n=change['page_number'];local=change['before_page_rune_ordinal']
        parts=wiki.copy();gaps=sections[n]['gaps'].copy();gaps[local]=change['source_gap']
        parts[n]=assemble(gaps,sections[n]['runes'])
        variant=tokenize(parts,alphabet)
        starts=set(variant['starts'])
        rows.append({key:value for key,value in change.items() if key!='page_number'} | {
            'token_count':variant['tokens'],'token_count_delta':variant['tokens']-wiki_result['tokens'],
            'added_token_starts':sorted(starts-baseline_starts),
            'removed_token_starts':sorted(baseline_starts-starts),
            'long_tokens_10_plus':variant['long_tokens_10_plus'],
            'eleven_eleven_ten_windows':variant['eleven_eleven_ten_windows'],
            'histogram_changes':{str(length):variant['histogram'].get(str(length),0)-wiki_result['histogram'].get(str(length),0)
                                 for length in sorted({int(k) for k in variant['histogram']}|{int(k) for k in wiki_result['histogram']})
                                 if variant['histogram'].get(str(length),0)!=wiki_result['histogram'].get(str(length),0)}})
    return {'schema':'liberpedia-cross-source-word-boundaries-v1','plan_sha256':sha(plan_bytes),
            'comparison':'Archived seventh-onion LP2-00–55 versus wiki text. Both use identical ordered runes. Remove slash and CR/LF wraps, join pages, then apply the published rune-token rule.',
            'wiki':metrics(wiki_result),'source':metrics(source_result),
            'complete_source_added_token_starts':sorted(set(source_result['starts'])-baseline_starts),
            'complete_source_removed_token_starts':sorted(baseline_starts-set(source_result['starts'])),
            'non_rune_differences':len(rows),'one_gap_variants':rows,
            'limits':'The 33 gaps are cross-source differences, not independently verified image errors. This experiment tests one tokenizer and exact one-gap substitutions, not all punctuation-sensitive ciphers.'}


def figure(data):
    counts=Counter(row['page'] for row in data['one_gap_variants'])
    effects=Counter(row['page'] for row in data['one_gap_variants'] if row['added_token_starts'] or row['removed_token_starts'])
    pages=sorted(counts)
    height=126+len(pages)*21
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="660" height="{height}" viewBox="0 0 660 {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">Cross-source differences and LP2 token boundaries</title>',
           '<desc id="desc">Twenty-four LP2 pages contain 33 non-rune gap differences. No individual substitution changes a rune-token start under the stated tokenizer.</desc>',
           f'<rect width="660" height="{height}" fill="#faf9f5"/>',
           '<g font-family="Arial,sans-serif" fill="#263b45">',
           '<text x="20" y="31" font-size="21">Where the transcriptions differ</text>',
           '<text x="20" y="54" font-size="13">33 non-rune gaps on 24 LP2 pages · 0 move a token boundary</text>',
           '<text x="123" y="77" font-size="12">Differences</text>',
           '<text x="490" y="77" font-size="12">Changed token edges</text>']
    for i,page in enumerate(pages):
        y=89+i*21
        lines += [f'<text x="20" y="{y+13}" font-size="12">{page.upper()}</text>',
                  f'<rect x="123" y="{y+2}" width="{counts[page]*55}" height="15" fill="#315f73"/>',
                  f'<text x="{130+counts[page]*55}" y="{y+14}" font-size="12">{counts[page]}</text>',
                  f'<text x="513" y="{y+14}" font-size="12">{effects[page]}</text>']
    lines += [f'<text x="20" y="{height-13}" font-size="12">Different marks can still change a punctuation-aware or grid-based method.</text>','</g></svg>']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    result=report();chart=figure(result)
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        assert chart==(HERE/'boundary-effects.svg').read_text(encoding='utf-8')
        print('PASS: 33 cross-source gap variants, token effects and figure reproduce')
    else:
        (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        (HERE/'boundary-effects.svg').write_text(chart,encoding='utf-8',newline='\n')
        changed=sum(bool(row['added_token_starts'] or row['removed_token_starts']) for row in result['one_gap_variants'])
        print(json.dumps({'wiki':result['wiki'],'source':result['source'],'changed_gap_count':changed},ensure_ascii=False))


if __name__=='__main__':main()
