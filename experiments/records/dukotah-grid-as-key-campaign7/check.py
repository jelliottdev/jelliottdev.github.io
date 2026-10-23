"""Replay pinned Campaign VII functions and per-case paths independently of run.py.

The exact source dependencies are bundled under source/. All source programs
run from a temporary directory, so their saved result files stay intact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode=True

HERE=Path(__file__).resolve().parent
DEFAULT_SOURCE=HERE/'source'
REL=Path('corpus/H-branch-recovery/recovered/claude_master-roadmap-libra-qk527u')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def source_keys(a2,alt,b2):
    result={'A2_tokenpad':a2.keystreams()}
    tokens=alt.extract_tokens(); other={}
    for base in (59,60,62,64):
        pg={name:alt.decode(tokens[name],base) for name in ('p49','p50','p51')}
        other[f'b{base}_p49']=pg['p49']
        other[f'b{base}_p51']=pg['p51']
        other[f'b{base}_all']=pg['p49']+pg['p50']+pg['p51']
        other[f'b{base}_49+51']=pg['p49']+pg['p51']
    result['A2_altbase']=other
    onions=b2.onion_hex();token=a2.P49+a2.P50+a2.P51; xor={}
    for name,ob in onions.items():
        xor[f'token^{name}']=[a^b for a,b in zip(token,ob)]
        xor[name]=ob
    o234=[a^b^c for a,b,c in zip(onions['onion2'],onions['onion3'],onions['onion4'])]
    xor['onion2^3^4']=o234
    xor['token^onion2^3^4']=[a^b for a,b in zip(token,o234)]
    result['B2_onion_xor']=xor
    return result


def check_every_path(result,keys,pages,gp,ciphers,sc):
    targets=[(f'p{i:02d}',pg) for i,pg in enumerate(pages)]
    targets.append(('WHOLE',[c for pg in pages for c in pg]))
    for group, candidates in keys.items():
        phash=hashlib.sha256();shash=hashlib.sha256();n=0
        for name,raw in candidates.items():
            key=[v%29 for v in raw]
            for target,idxs in targets:
                runes=gp.indices_to_runes(idxs)
                for sign in (-1,1):
                    for atb in (False,True):
                        stream=ciphers.repeat_key(key,len(idxs))
                        noint=[((28-c if atb else c)+sign*stream[i])%29 for i,c in enumerate(idxs)]
                        plain0=gp.indices_to_translit(noint)
                        plain1,_=ciphers.transform_runes(
                            runes,lambda L,k=key:ciphers.repeat_key(k,L),
                            sign=sign,interrupters=True,atbash=atb)
                        for interrupt,plaintext in ((False,plain0),(True,plain1)):
                            method=f'sign{sign:+d} atb{int(atb)} '+('INT' if interrupt else 'noint')
                            phash.update(f'{name}\t{target}\t{method}\t{plaintext}\n'.encode('utf-8'))
                            value=sc.score_norm(plaintext)
                            shash.update(f'{name}\t{target}\t{method}\t{value:.6f}\n'.encode('ascii'))
                            n+=1
        saved=result['groups'][group]
        assert n==saved['case_count']
        assert phash.hexdigest()==saved['plaintext_digest_sha256'],group
        assert shash.hexdigest()==saved['score_digest_sha256'],group


def check_plants(rows,key,gp,ciphers,sc):
    phrase='THEPRIMESARESACREDANDTHETOTIENTFUNCTIONISSACREDALLTHINGSSHOULDBEENCRYPTED'
    base=gp.keyword_to_indices(phrase)
    known=(base*(1+120//len(base)))[:120]
    assert len(rows)==8
    for row in rows:
        sign=row['sign'];atb=row['atbash'];interrupt=row['interrupt']
        cipher=[];expected=[];clock=0;forced=0
        for p in known:
            if interrupt and p==0:
                cipher.append(0);expected.append(0);continue
            transformed=(p-sign*key[clock%len(key)])%29
            c=28-transformed if atb else transformed
            if interrupt and c==0:
                cipher.append(0);expected.append(0);forced+=(p!=0)
            else:
                cipher.append(c);expected.append(p);clock+=1
        actual,_=ciphers.transform_runes(
            gp.indices_to_runes(cipher),lambda L,k=key:ciphers.repeat_key(k,L),
            sign=sign,atbash=atb,interrupters=interrupt)
        assert actual==gp.indices_to_translit(expected)
        assert row['ciphertext_sha256']==hashlib.sha256(bytes(cipher)).hexdigest()
        assert row['constructed_plaintext_sha256']==hashlib.sha256(bytes(expected)).hexdigest()
        assert row['forced_literal_F']==forced
        assert row['unchanged_known_runes']==120-forced
        assert row['f_runes']==cipher.count(0)
        assert row['length']==120 and row['exact']
        assert row['score']==round(sc.score_norm(actual),6)
        assert row['pass_threshold']==(sc.score_norm(actual)>-5.2)
        assert row['pass_threshold']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-root',type=Path,default=DEFAULT_SOURCE)
    ap.add_argument('--check-site',action='store_true',help='also compare every local site page JSON')
    args=ap.parse_args()
    source=args.source_root.resolve()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    inp=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    tokens = [token for page in inp['raw_tokens'].values() for token in page]
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    invalid59 = [token for token in tokens if any(alphabet.index(c) >= 59 for c in token)]
    assert sorted(invalid59) == ['0x', '0x', '0x', '2x'] and '4F' in tokens
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    for row in plan['source_paths_and_sha256']:
        assert sha(source/row['path'])==row['sha256'], row['path']
    assert sha(HERE/'inputs.json')==plan['input_manifest_sha256']
    assert sha(HERE/'input-indices.bin')==plan['index_stream_sha256']
    assert sha(HERE/'page-lengths.json')==plan['page_lengths_sha256']
    src=source/'liber-primus'
    sys.path[:0]=[str(src/'src'),str(src/'analysis')]
    from lp import gematria as gp
    from lp import ciphers,score
    from run_stats import load_pages
    source_pages=load_pages()[:-2]
    boundaries=json.loads((HERE/'page-lengths.json').read_text(encoding='utf-8'))
    assert len(source_pages)==len(boundaries['ids'])==55
    assert [len(p) for p in source_pages]==boundaries['lengths']
    assert bytes(i for page in source_pages for i in page)==(HERE/'input-indices.bin').read_bytes()
    if args.check_site:
        root=HERE.parents[2]
        for ident, indices in zip(boundaries['ids'],source_pages):
            site=json.loads((root/'data/pages'/f'{ident}.json').read_text(encoding='utf-8'))
            assert gp.runes_to_indices(site['raw'])==indices, ident
    community=source/REL/'sources/community'
    with tempfile.TemporaryDirectory(prefix='campaign7-grid-') as temp:
        pkg=Path(temp)/'campaign7';pkg.mkdir()
        (pkg/'__init__.py').write_text('',encoding='ascii')
        for short in ('a2_tokenpad','a2_altbase','b2_onion_xor'):
            shutil.copyfile(source/REL/'liber-primus/analysis/campaign7'/f'{short}.py',pkg/f'{short}.py')
        sys.path.insert(0,temp)
        a2=importlib.import_module('campaign7.a2_tokenpad')
        alt=importlib.import_module('campaign7.a2_altbase')
        b2=importlib.import_module('campaign7.b2_onion_xor')
        alt.SRC=str(community/'scream314_liber_primus.md')
        b2.Y2014=str(community/'scream314_2014.md')
        # Source parsing, not a second reading of our bundled arrays.
        assert a2.P49==inp['archived_pages']['p49']
        assert a2.P50==inp['archived_pages']['p50']
        assert a2.P51==inp['archived_pages']['p51']
        assert alt.extract_tokens()==inp['raw_tokens']
        for k,v in b2.onion_hex().items():
            assert bytes(v).hex()==inp['onion_hex'][k]
        cases={'A2_tokenpad':a2.run(), 'A2_altbase':alt.run(),
               'B2_onion_xor':b2.run()}
        files={'A2_tokenpad':'a2_tokenpad_results.json',
               'A2_altbase':'a2_altbase_results.json',
               'B2_onion_xor':'b2_onion_xor_results.json'}
        for group, source_out in cases.items():
            old=json.loads((HERE/f'source-{files[group]}').read_text(encoding='utf-8'))
            assert json.loads(json.dumps(source_out))==old, (group,'source result drift')
            local=result['groups'][group]
            assert round(local['best']['score'],3)==old['best_score']
            assert local['n_hits']==old['n_hits']
            assert local['per_key_best']==old['per_key_best']
            for field in ('key','target','method','plaintext'):
                assert local['best'][field]==old['best'][field]
            assert local['case_count']==len(local['per_key_best'])*56*8
        assert result['case_count']==14784
        assert result['xor_forensics']==cases['B2_onion_xor']['xor_forensics']
        assert {str(k):v for k,v in cases['A2_altbase']['base_report'].items()}==result['base_report']
        check_every_path(result,source_keys(a2,alt,b2),source_pages,gp,ciphers,score.default())
        check_plants(result['controls'],a2.P49+a2.P50+a2.P51,gp,ciphers,score.default())
    print('PASS: source replay, all 14,784 plaintext/score paths, 8 constructed-message controls')


if __name__=='__main__':main()
