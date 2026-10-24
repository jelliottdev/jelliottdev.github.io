"""Independent standard-library recount: no producer or source module imports."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
S=H.parents[3]/'source-cache/dukotah-cicada3301'
p=json.loads((H/'plan-frozen.json').read_text()); r=json.loads((H/'length-results.json').read_text())
assert r['plan_sha256']==hashlib.sha256((H/'plan-frozen.json').read_bytes()).hexdigest()
for x in p['inputs']: assert hashlib.sha256((S/x['path']).read_bytes()).hexdigest()==x['sha256']
alphabet=set('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ')
words=[]; fc=0
for page in (S/'liber-primus/data/krisyotam_runes.txt').read_text(encoding='utf-8').split('%')[:55]:
    for piece in re.split('[-.]',page):
        v=[c for c in piece if c in alphabet]
        if v: words.append(len(v)); fc+=v.count('ᚠ')
n=len(words); total=sum(words)
assert (n,total,fc)==(r['lp2']['words'],r['lp2']['runes'],r['lp2']['F'])
def encode(w):
    # Different implementation: longest-match regular expression tokenization.
    return len(re.findall('ING|EA|IA|IO|AE|OE|NG|EO|TH|[A-Z]',w.upper()))
known='PARABLE LIKE THE INSTAR TUNNELING TO THE SURFACE WE MUST SHED OUR OWN CIRCUMFERENCES FIND THE DIVINITY WITHIN AND EMERGE'.split()
assert list(map(encode,known))==[7,4,2,6,7,2,2,7,2,4,4,3,3,14,4,2,8,5,3,6]
for row in r['rows']:
    v=[x for x in map(encode,re.findall(r"[A-Za-z']+",(S/row['path']).read_text(encoding='utf-8',errors='ignore'))) if x]
    assert len(v)==row['words']
    assert (len(v)>=2*n)==row['eligible']
    if not row['eligible']: continue
    # Rolling integer sums, then select the source's sampled offsets.
    current=sum(v[:n]); all_sums=[current]
    for i in range(n,len(v)):
        current+=v[i]-v[i-n]; all_sums.append(current)
    offsets=list(range(0,len(v)-n,max(1,(len(v)-n)//4000)))
    sums=[all_sums[i] for i in offsets]
    assert len(sums)==row['sampled_passages']
    assert min(sums)/n==row['minimum'] and max(sums)/n==row['maximum']
    assert sum(x>=total-fc for x in sums)==row['lower_reaching']
    assert sum(x>=total for x in sums)==row['upper_reaching']
    assert hashlib.sha256(','.join(map(str,sums)).encode()).hexdigest()==row['sampled_sums_sha256']
print('PASS: exact pinned bytes; independent tokenizer, encoder, and every sampled passage at both endpoints.')
