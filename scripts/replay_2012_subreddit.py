"""Compare two explicit post-selection rules for the archived 2012 book code."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'exports/sources/cicada-2012'
KEY = [int(c, 36) for c in 'a2e7j6ic78h0j7eiejd0120']


def decode(text):
    result=[]
    position=0
    for char in text:
        if char.isascii() and char.isalpha():
            output=(ord(char.upper())-65-KEY[position % len(KEY)]) % 26
            assert (output+KEY[position % len(KEY)]) % 26 == ord(char.upper())-65
            result.append(chr(output+65))
            position+=1
        else:
            result.append(char)
    return ''.join(result)


def calculate():
    paths=['subreddit-posts.json','retrieved-payload.bin']
    hashes={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in paths}
    manifest=json.loads((SOURCE/'manifest.json').read_bytes())
    assert all(hashes[n]==next(x['sha256'] for x in manifest['files'] if x['file']==n) for n in paths)
    posts=sorted(json.loads((SOURCE/paths[0]).read_bytes())['data'],key=lambda p:(p['created_utc'],p['id']))
    coordinates=[tuple(map(int,x)) for x in re.findall(rb'(?m)^(\d+):(\d+)$',(SOURCE/paths[1]).read_bytes())]
    assert len(coordinates)==76
    variants={}
    for mode in ['all-earliest','named-author']:
        selected=[];decisions=[];seen=set()
        for post in posts:
            title=post['title'].strip()
            reason='included'
            if post['url'].lower().endswith(('.jpg','.png')):
                reason='image URL'
            elif mode=='named-author' and post['author']!='CageThrottleUs':
                reason='different author field'
            elif title in seen:
                reason='duplicate stripped title'
            if reason=='included':
                seen.add(title)
                selected.append({'line':len(selected)+1,'post_id':post['id'],
                                 'created_utc':post['created_utc'],'author':post['author'],
                                 'original_title':post['title'],'working_title':title,'decoded':decode(title)})
            decisions.append({'post_id':post['id'],'decision':reason})
        lookups=[]
        for row,col in coordinates:
            source=selected[row-1]
            character=source['decoded'][col-1]
            # Iterator counting checks the direct indexing path.
            assert character==next(c for i,c in enumerate(source['decoded'],1) if i==col)
            lookups.append({'coordinate':[row,col],'post_id':source['post_id'],
                            'decoded_line':source['decoded'],'character':character})
        variants[mode]={'selected_lines':selected,'decisions':decisions,'lookups':lookups,
                        'raw_output':''.join(x['character'] for x in lookups)}
    assert variants['all-earliest']['raw_output'].startswith('CAMT US')
    assert variants['named-author']['raw_output']=='CALL US AT US TELE PHONE NUMBER TWO ONE FOUR THREE NINE OH NINE SIX OH EIGHT'
    return {'source_sha256':hashes,'posts':len(posts),'key':KEY,'variants':variants,
            'selection_disclosure':'Exploratory comparison motivated by a reported ordering discrepancy; not a blind test.',
            'rules':'Sort timestamp then ID; exclude image URLs; strip outer whitespace; retain internal punctuation/spacing; reset key per title; advance only ASCII letters; uppercase decoded letters. Coordinate indices start at one.',
            'limits':'No author authentication, original API retrieval or signature check. Current archived spacing is retained; historical spacing repairs are not reproduced. No telephone number contacted.',
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    report=calculate()
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    for name,result in report['variants'].items():print(name, len(result['selected_lines']),result['raw_output'])
