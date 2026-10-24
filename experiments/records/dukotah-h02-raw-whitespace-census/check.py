"""Independent delimiter/regex census, plus optional isolated GPG whitespace control."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
G02=HERE.parent/'dukotah-g02-signature-corpus'
def sha(x): return hashlib.sha256(x).hexdigest()
def save(name,x): (HERE/name).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def main(gpg):
    result=json.loads((HERE/'results.json').read_text())
    aliases=json.loads((G02/'sources/path-aliases.json').read_text())['paths']
    bodies={}; canonical=collections.defaultdict(list); cases=[]
    pattern=re.compile(rb'(?:\A|(?<=[\r\n]))-----BEGIN PGP SIGNED MESSAGE-----(?:\r\n|\n|\r)((?:Hash: [^\r\n]+(?:\r\n|\n|\r))+)(?:\r\n|\n|\r)(.*?)(?:(?<=\n)|(?<=\r))-----BEGIN PGP SIGNATURE-----(?:\r\n|\n|\r).*?-----END PGP SIGNATURE-----',re.S)
    with zipfile.ZipFile(G02/'sources/asc-blobs.zip') as z:
        for entry in aliases:
            raw=z.read('blobs/'+entry['sha256'])
            for bi,match in enumerate(pattern.finditer(raw)):
                body=match.group(2)
                ls=re.split(rb'\r\n|\r|\n',body)
                if ls[-1] == b'': ls.pop()
                suffix=[re.search(rb'[ \t]*$',ln).group() for ln in ls]
                counts=[len(s) for s in suffix if s]
                receipts=[{'line':i+1,'spaces':s.count(b' '),'tabs':s.count(b'\t')} for i,s in enumerate(suffix) if s]
                saved=next(r for r in result['rows'] if r['path']==entry['path'] and r['block']==bi)
                assert saved['exact_body_sha256']==sha(body)
                assert saved['line_count']==len(ls) and saved['nonzero_counts']==counts
                assert receipts==[{k:r[k] for k in ('line','spaces','tabs')} for r in saved['nonzero_lines']]
                bodies[sha(body)]=(ls,suffix)
                normalized=b'\n'.join(re.sub(rb'^- ',b'',ln).rstrip(b' \t') for ln in ls)
                canonical[sha(normalized)].append({'path':entry['path'],'body_sha256':sha(body),'counts':counts,
                                                  'lf_body_sha256':sha(b'\n'.join(ls))})
                cases.append((entry['path'],bi))
        assert sorted(cases)==sorted((r['path'],r['block']) for r in result['rows'])
        assert len(bodies)==result['exact_unique_bodies'] and len(canonical)==result['canonical_unique_bodies']
        groups=[]
        for digest,rows in canonical.items():
            if len(set(r['body_sha256'] for r in rows))>1:
                groups.append({'canonical_body_sha256':digest,'exact_variants':len(set(r['body_sha256'] for r in rows)),
                               'line_ending_only':len(set(r['lf_body_sha256'] for r in rows))==1,
                               'trailing_whitespace_differs':len(set(tuple(r['counts']) for r in rows))>1,
                               'paths':[r['path'] for r in rows]})
        receipt={'pass':True,'independently_parsed_blocks':len(cases),'independent_exact_bodies':len(bodies),
                 'independent_canonical_bodies':len(canonical),'compared_every_sparse_line_receipt':True,
                 'canonical_variant_groups':groups}
        if gpg:
            keypath='corpus/A-primary-artifacts/pgp/keys/cicada-3301-pubkey.keyserver.ubuntu.com.asc'
            message=next(r for r in result['rows'] if r['g02_verdict']=='PASS')
            entry=next(x for x in aliases if x['path']==keypath)
            public=z.read('blobs/'+entry['sha256'])
            raw=z.read('blobs/'+message['raw_sha256'])
            m=pattern.search(raw); original_body=m.group(2)
            modified=re.sub(rb'([^\r\n]+)(\r\n|\n|\r)',rb'\1 \t\2',original_body,count=1)
            assert modified!=original_body
            edited=raw[:m.start(2)]+modified+raw[m.end(2):]
            with tempfile.TemporaryDirectory(prefix='h02-public-gpg-') as temp:
                home=Path(temp); (home/'key.asc').write_bytes(public)
                base=['gpg','--homedir',str(home),'--batch','--no-tty','--allow-weak-digest-algos']
                imported=subprocess.run(base+['--import',str(home/'key.asc')],capture_output=True)
                assert imported.returncode==0
                observations=[]
                for label,data in [('original',raw),('trailing_space_tab_added',edited)]:
                    path=home/(label+'.asc');path.write_bytes(data)
                    p=subprocess.run(base+['--status-fd','1','--verify',str(path)],capture_output=True)
                    status=p.stdout.decode('utf-8',errors='replace')
                    fingerprint='6D854CD7933322A601C3286D181F01E57A35090F'
                    assert p.returncode==0 and 'VALIDSIG '+fingerprint in status,(p.returncode,status)
                    observations.append({'variant':label,'sha256':sha(data),'returncode':p.returncode,'validsig_fingerprint':fingerprint})
                save('gpg-control.json',{'source_path':message['path'],'edit':'Add space then tab to first nonempty body line; signature bytes unchanged.',
                                         'isolated_public_key_home':True,'observations':observations})
    save('independent-check.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='canonical_variant_groups'},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gpg-control',action='store_true');main(ap.parse_args().gpg_control)
