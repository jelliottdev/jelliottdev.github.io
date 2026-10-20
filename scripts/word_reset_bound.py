"""Count exact and anagram repeats under two explicit token boundary policies."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/word-reset-bound.json'


def tokenize(raw, lookup, apostrophe):
    transparent = '/\r\n' + ("'" if apostrophe else '')
    tokens, current, offsets = [], [], []
    for offset, c in enumerate(raw):
        if c in lookup:
            current.append(lookup[c]); offsets.append(offset)
        elif c not in transparent and current:
            tokens.append(dict(indices=current, source_offsets=offsets))
            current, offsets = [], []
    if current:
        tokens.append(dict(indices=current, source_offsets=offsets))
    return tokens


def report():
    paths = ['data/index.json'] + [f'text/lp2-{n:02}.txt' for n in range(56)]
    blobs = {p:(ROOT / p).read_bytes() for p in paths}
    lookup = {a['rune']:i for i,a in enumerate(json.loads(blobs[paths[0]])['alphabet'])}
    policies = []
    for apostrophe in (False,True):
        selected, counts = [], []
        for path in paths[1:]:
            raw = blobs[path].decode('utf-8-sig')
            unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
            if unknown:
                raise ValueError(f'Unknown runes: {unknown}')
            tokens = tokenize(raw,lookup,apostrophe)
            interior = tokens[1:-1]
            counts.append(dict(page=Path(path).stem,all_tokens=len(tokens),
                               interior_tokens=len(interior),selected_ge4=sum(len(t['indices'])>=4 for t in interior)))
            for ordinal,t in enumerate(interior,1):
                if len(t['indices'])>=4:
                    selected.append(dict(page=Path(path).stem,token_index=ordinal,**t))
        exact, anagram = defaultdict(list), defaultdict(list)
        for t in selected:
            location=dict(page=t['page'],token_index=t['token_index'])
            exact[tuple(t['indices'])].append(location)
            anagram[tuple(sorted(t['indices']))].append(location)
        def collisions(groups):
            return [dict(signature=list(k),occurrences=v,pairs=len(v)*(len(v)-1)//2)
                    for k,v in sorted(groups.items()) if len(v)>1]
        e,a=collisions(exact),collisions(anagram)
        policies.append(dict(apostrophe='transparent' if apostrophe else 'boundary',
                             selected_tokens=len(selected),distinct_exact=len(exact),
                             exact_pairs=sum(g['pairs'] for g in e),
                             anagram_pairs_ge4=sum(g['pairs'] for g in a),
                             anagram_pairs_ge5=sum(g['pairs'] for g in a if len(g['signature'])>=5),
                             exact_collisions=e,anagram_collisions=a,page_counts=counts,tokens=selected))
    return dict(schema='liberpedia-word-reset-bound-v1',
                scope='LP2-00–55 archived text; slash and CR/LF are transparent; all other nonrunes delimit tokens except apostrophe in the transparent variant. Omit first and last nonempty token per page; retain headings otherwise; select ciphertext tokens with >=4 runes.',
                positions='Zero-based token ordinals within each original page token list and zero-based Unicode source offsets; page edges are never joined.',
                input_sha256={p:hashlib.sha256(b).hexdigest() for p,b in blobs.items()},policies=policies,
                limits='No claim that unknown plaintext repeats. Exact repeats constrain only a shared deterministic word function with identical key/reset context. Anagrams constrain a shared symbol map with one output per input rune plus arbitrary within-word permutation. Changing maps, contexts or boundaries requires another test.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();r=report()
    if args.check:
        assert r==json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: both token policies, exact repeats, anagram pairs and source positions')
    else:
        print(json.dumps(r,ensure_ascii=False,indent=2))
