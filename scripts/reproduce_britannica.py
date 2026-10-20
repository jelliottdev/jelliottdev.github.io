"""Replay the archived Britannica coordinates without changing source wrapping.

--check requires only Python. --verify-signature additionally requires GnuPG
and verifies the preserved clue in a fresh temporary keyring, offline.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
TEXT='exports/sources/gutenberg-31447-8.txt'
CLUE='exports/sources/britannica-2012-clue.asc'
KEY='exports/steganography/cicada-public-key.asc'
OUTPUT=ROOT/'exports/britannica-book-code.json'
FINGERPRINT='6D854CD7933322A601C3286D181F01E57A35090F'


def report():
    blobs={p:(ROOT/p).read_bytes() for p in [TEXT,CLUE]}
    text=blobs[TEXT].decode('latin1')
    heading='CICADA (_Cicadidae_)'
    assert text.count(heading)==1
    lines=text[text.index(heading):].splitlines()
    message=blobs[CLUE].decode('utf-8')
    body=message.split('-----BEGIN PGP SIGNATURE-----')[0]
    codes=[line.strip() for line in body.splitlines() if re.fullmatch(r'\d+:\d+',line.strip())
           or line.strip() in ['the product of the first two primes','the first prime']]
    assert len(codes)==22 and sum(':' in c for c in codes)==19
    comparisons=[];trace=[]
    for heading_counted in [True,False]:
        for column_base in [0,1]:
            run=[]
            for instruction in codes:
                if ':' in instruction:
                    row,col=map(int,instruction.split(':'))
                    i=row-1 if heading_counted else row
                    j=col-column_base
                    in_bounds=0<=i<len(lines) and 0<=j<len(lines[i])
                    run.append(dict(instruction=instruction,line_index=i,character_index=j,
                                    source_line=lines[i],in_bounds=in_bounds,output=lines[i][j] if in_bounds else '?'))
                else:
                    run.append(dict(instruction=instruction,output=str(2*3 if 'product' in instruction else 2)))
            result=''.join(t['output'] for t in run)
            comparisons.append(dict(heading_counted=heading_counted,column_base=column_base,output=result,out_of_range=sum(t.get('in_bounds') is False for t in run)))
            if not heading_counted and column_base==1:
                trace=run;raw=result
    assert raw=='eq6emgv2eHsrix6t.onion'
    return dict(schema='liberpedia-britannica-book-code-v1',
                input_sha256={p:hashlib.sha256(b).hexdigest() for p,b in blobs.items()},
                source_url='https://www.gutenberg.org/files/31447/31447-8.txt',
                method='CICADA heading is line zero; next physical line is line one; columns one-based; preserve spaces, punctuation, underscores, line wraps and case. Latin-1 decoding. Prime instructions emit decimal 6, 2, 6.',
                codes=codes,coordinate_count=19,literal_instruction_count=3,
                raw_output=raw,lowercase_rendering=raw.lower(),trace=trace,
                numbering_comparisons=comparisons,
                limits='Extraction from these preserved bytes, not a verified 2012 Gutenberg snapshot. No claim of successful historical service access, identity, or an LP decryption. Signature verification is a separate optional command. No reconstruction of the Mabinogion clue is included.')


def verify_signature():
    with tempfile.TemporaryDirectory(prefix='liberpedia-britannica-') as directory:
        base=['gpg','--no-options','--homedir',directory,'--batch','--no-auto-key-retrieve']
        subprocess.run(base+['--import',str(ROOT/KEY)],check=True,capture_output=True)
        result=subprocess.run(base+['--allow-weak-digest-algos','--status-fd','1','--verify',str(ROOT/CLUE)],capture_output=True,text=True)
        valid=[line.split() for line in result.stdout.splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
        assert result.returncode==0 and len(valid)==1 and valid[0][2]==FINGERPRINT,result.stdout+result.stderr
        print(json.dumps(dict(fingerprint=FINGERPRINT,exit_code=result.returncode,
                             input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [CLUE,KEY]},
                             status=result.stdout,method='Offline isolated GnuPG keyring; explicit historical SHA-1 compatibility. A valid signature binds the message to the key, not a civil identity or independently established timestamp.'),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--check',action='store_true')
    group.add_argument('--verify-signature',action='store_true')
    args=parser.parse_args()
    if args.verify_signature:
        verify_signature()
    else:
        result=report()
        if args.check:
            assert result==json.loads(OUTPUT.read_text(encoding='utf-8'))
            print('PASS: 19 coordinates, three literal instructions, raw case and four numbering comparisons')
        else:
            print(json.dumps(result,ensure_ascii=False,indent=2))
