"""Independently check the preserved source Step 0 against explicit book parts."""
import base64,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
plan=json.loads((HERE/'plan.json').read_bytes())
for r in plan['inputs']: assert hashlib.sha256((HERE.parents[2]/r['path']).read_bytes()).hexdigest()==r['sha256']
raw=(HERE/'source-lp.md').read_text(encoding='utf8')
text='\n'.join(l[4:] if l.startswith('    ') else l for l in raw.splitlines())
headings=list(re.finditer(r'(?m)^(#{1,2}) (.+)$',text))
rows=[]
for m in re.finditer(r'-----BEGIN PGP SIGNATURE-----\n(.*?)-----END PGP SIGNATURE-----',text,re.S):
 lines=m.group(1).split('\n\n',1)[1].splitlines(); payload=base64.b64decode(''.join(l for l in lines if l and not l.startswith('=')))
 h=payload[0]
 if h&64:
  n=payload[1]
  if n<192: off=2; size=n
  elif n<224: off=3; size=(n-192)*256+payload[2]+192
  elif n==255: off=6; size=int.from_bytes(payload[2:6],'big')
  else: raise ValueError('partial length outside pinned input scope')
 else:
  width={0:1,1:2,2:4}[h&3];off=1+width;size=int.from_bytes(payload[1:off],'big')
 d=payload[off:off+size];assert d[0]==4
 sub=d[6:6+int.from_bytes(d[4:6],'big')];times=[]
 while sub:
  n=sub[0];assert n<192
  item=sub[1:1+n];sub=sub[1+n:]
  if item[0]&127==2:times.append(int.from_bytes(item[1:],'big'))
 assert len(times)==1
 prior=[h for h in headings if h.start()<m.start()]
 rows.append({'part':next(h.group(2) for h in reversed(prior) if h.group(1)=='#'),'section':prior[-1].group(2),'sig_creation_unix':times[0]})
source=json.loads((HERE/'source-replay.json').read_bytes())
assert [(r['section'],r['sig_creation_unix']) for r in rows]==[(r['section'],r['sig_creation_unix']) for r in source['signed_blocks']]
lp2=text.split('# LP2\n',1)[1].split('# Magic Squares',1)[0]
runes=(HERE/'source-runes.txt').read_text(encoding='utf8')
result={'signed_blocks':len(rows),'distinct_timestamp_seconds':len({r['sig_creation_unix'] for r in rows}),'LP1_signed_blocks':sum(r['part']=='LP1' for r in rows),'LP2_signed_blocks':sum(r['part']=='LP2' for r in rows),'LP2_grouped_headings':len(re.findall(r'(?m)^## ',lp2)),'LP2_signature_markers':lp2.count('-----BEGIN PGP SIGNATURE-----'),'runic_transcription_segments':runes.count('%')+1,'runic_signature_markers':runes.count('-----BEGIN PGP SIGNATURE-----'),'rows':rows,'source_step0_matches':True,'conclusion':'These textual inputs provide no per-target-page signature timestamp join. They cannot establish absence in all historical artifacts.'}
assert (result['signed_blocks'],result['LP1_signed_blocks'],result['LP2_signature_markers'],result['runic_transcription_segments'])==(8,8,0,57)
(HERE/'independent-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
