"""Independent C-01 normalization, exact RNG reconstruction and integer interval counts."""
import re,hashlib,ast
from pathlib import Path
import numpy as np
MULTI=('ING','EA','IA','IO','AE','OE','NG','EO','TH')
sha=lambda b:hashlib.sha256(b).hexdigest()
ah=lambda a:sha(np.asarray(a,dtype='<i2').tobytes())

def normalize(raw,path):
    text=raw.decode('utf-8',errors='ignore')
    if str(path).lower().endswith(('.html','.htm','.xml')) or '<html' in text[:4000].lower():
        text=re.sub(r'<(script|style)\b.*?</\1>',' ',text,flags=re.S|re.I)
        text=re.sub(r'<[^>]+>',' ',text)
        for a,b in [('&nbsp;',' '),('&amp;','&'),('&quot;','"'),('&#39;',"'")]:text=text.replace(a,b)
    start=re.search(r'\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG[^\n]*\n',text)
    if start:text=text[start.end():]
    end=re.search(r'\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG',text)
    if end:text=text[:end.start()]
    text=text.upper()
    for j,m in enumerate(MULTI):text=text.replace(m,chr(j+1))
    words=re.findall(r"[A-Z\x01-\x09\-']+",text)
    values=[sum(c not in "'-" for c in word) for word in words]
    return np.array([v for v in values if v],dtype=np.int16)

def manuscript(raw,gp_source):
    tree=ast.parse(gp_source.read_text(encoding='utf-8'))
    table=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GEMATRIA' for t in n.targets)))
    runes={r[1] for r in table};f=table[0][1];lengths=[];fs=[]
    for segment in raw.decode('utf-8').split('%')[:55]:
        current=0;fc=0
        for ch in segment:
            if ch in runes:current+=1;fc+=int(ch==f)
            elif ch in '-.':
                if current:lengths.append(current);fs.append(fc)
                current=0;fc=0
        if current:lengths.append(current);fs.append(fc)
    return np.array(lengths,dtype=np.int16),np.array(fs,dtype=np.int16)

def patterns(obs,fc):
    rng=np.random.default_rng(3301)
    for _ in range(4):rng.permutation(len(obs))
    out={}
    for w in (400,120):
        out[f'realW{w}:interval']=(obs[:w].copy(),fc[:w].copy())
        for j in range(2):
            order=rng.permutation(w)
            out[f'n{j}W{w}:interval']=(obs[:w][order],fc[:w][order])
    return out

def count(values,obs,fc):
    if len(values)<len(obs):return np.empty(0,dtype=np.int64)
    windows=np.lib.stride_tricks.sliding_window_view(values,len(obs))
    lo=np.maximum(1,obs.astype(np.int64)-fc);hi=np.minimum(40,obs)
    valid=(obs>=1)&(obs<=29)  # groups_interval only emits observed values1..29
    return ((windows>=lo)&(windows<=hi)&valid).sum(axis=1,dtype=np.int64)
