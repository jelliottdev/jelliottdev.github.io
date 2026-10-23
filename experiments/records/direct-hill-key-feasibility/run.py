"""Complete direct Hill-key feasibility for fixed twelve-rune page openings."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LOOKUP = {r: i for i, r in enumerate(ALPHABET)}
Q = 29


def rank(columns, n, q=Q):
    """Rank of column vectors by modular row elimination."""
    if not columns:
        return 0
    rows = [[column[i] % q for column in columns] for i in range(n)]
    pivot_row = 0
    for col in range(len(columns)):
        pivot = next((i for i in range(pivot_row, n) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        inv = pow(rows[pivot_row][col], -1, q)
        rows[pivot_row] = [(v * inv) % q for v in rows[pivot_row]]
        for i in range(n):
            if i != pivot_row and rows[i][col]:
                factor = rows[i][col]
                rows[i] = [(x - factor * y) % q for x, y in zip(rows[i], rows[pivot_row])]
        pivot_row += 1
        if pivot_row == n:
            break
    return pivot_row


def coefficients(basis, vector, n, q=Q):
    """Solve basis*a=vector for an independent basis, or return None."""
    width = len(basis)
    if width == 0:
        return [] if all(v % q == 0 for v in vector) else None
    rows = [[basis[j][i] % q for j in range(width)] + [vector[i] % q] for i in range(n)]
    pivots = []
    r = 0
    for col in range(width):
        pivot = next((i for i in range(r, n) if rows[i][col]), None)
        if pivot is None:
            raise AssertionError('Basis is dependent')
        rows[r], rows[pivot] = rows[pivot], rows[r]
        inv = pow(rows[r][col], -1, q)
        rows[r] = [(x * inv) % q for x in rows[r]]
        for i in range(n):
            if i != r and rows[i][col]:
                factor = rows[i][col]
                rows[i] = [(x - factor*y) % q for x,y in zip(rows[i], rows[r])]
        pivots.append(col)
        r += 1
    if any(rows[i][-1] for i in range(r,n)):
        return None
    return [rows[i][-1] for i in range(width)]


def feasible(cipher, plain, n, q=Q):
    """Check every dependency with a ciphertext basis and an independent image basis."""
    assert len(cipher) == len(plain) and len(cipher) % n == 0
    cblocks = [cipher[i:i+n] for i in range(0,len(cipher),n)]
    pblocks = [plain[i:i+n] for i in range(0,len(plain),n)]
    cipher_rank = rank(cblocks,n,q)
    basis_c, basis_p = [], []
    for c,p in zip(cblocks,pblocks):
        coeff = coefficients(basis_c,c,n,q)
        if coeff is None:
            basis_c.append(c)
            basis_p.append(p)
        elif any(sum(a * b[i] for a,b in zip(coeff,basis_p)) % q != p[i] % q for i in range(n)):
            return cipher_rank, 0, 'dependency-mismatch'
    r = len(basis_c)
    if rank(basis_p,n,q) != r:
        return r, 0, 'noninjective-image'
    count = 1
    for j in range(r,n):
        count *= q**n - q**j
    return r, count, 'feasible'


def inputs():
    plan = json.loads((ROOT/'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))
    openings = [(o['id'],o['indices']) for o in plan['openings']]
    pages = []
    for number in range(56):
        page_id = f'lp2-{number:02d}'
        raw = (ROOT/'text'/f'{page_id}.txt').read_text(encoding='utf-8')
        indices = [LOOKUP[ch] for ch in raw if ch in LOOKUP]
        if indices:
            if len(indices)<12:
                raise ValueError(f'{page_id} has too few runes')
            pages.append((page_id,indices[:12]))
    assert len(pages)==55 and len(openings)==9
    return pages,openings


def make_results():
    pages,openings=inputs()
    cases=[]
    summary={}
    for n in (2,3):
        status_counts={}
        c_rank_counts={}
        key_count_sum=0
        for page_id,cipher in pages:
            for opening_id,plain in openings:
                r,count,status=feasible(cipher,plain,n)
                cases.append({'dimension':n,'page':page_id,'opening':opening_id,
                              'cipher_rank':r,'status':status,'compatible_key_count':count})
                status_counts[status]=status_counts.get(status,0)+1
                c_rank_counts[str(r)]=c_rank_counts.get(str(r),0)+1
                key_count_sum+=count
        summary[str(n)]={'cases':len(pages)*len(openings),'status_counts':status_counts,
                         'cipher_rank_counts':c_rank_counts,'compatible_key_count_sum':key_count_sum}
    return {'schema':'liberpedia-direct-hill-feasibility-results-v1','field':29,
            'page_count':len(pages),'opening_count':len(openings),
            'total_cases':len(cases),'summary':summary,'cases':cases}


def write(result):
    (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=make_results()
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('PASS: complete Hill feasibility cases match stored results')
    else:
        write(result)
        print(json.dumps(result['summary'],indent=2))
