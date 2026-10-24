"""Source-exact stable beam representation, compiled; no target input loading."""
import ast,importlib.util,json,sys
from pathlib import Path
import numpy as np
from numba import njit
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;LP=H/'source/liber-primus'
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
gp=module('keyword_gp',LP/'src/lp/gematria.py');sc=module('keyword_score',LP/'src/lp/score.py');Q=sc.Quadgram(str(LP/'data/english_quadgrams.txt'))
def definitions(path,names,env):
    nodes=[n for n in ast.parse(path.read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),env)
env={'gp':gp,'N':29,'Q':Q,'_QD':Q.d,'_QF':Q.floor,'_TR':gp.IDX_TO_TRANS,'MAXSKIP':3,'np':np,'random':__import__('random')}
definitions(LP/'analysis/campaign18_skip/skipdecode.py',['_ALIAS','eng_to_idx','idx_to_trans','encipher_keyskip'],env)
definitions(LP/'analysis/campaign18_skip/sweep.py',['_qdelta','beam'],env)
native=env['beam'];env['beam']=native
definitions(LP/'analysis/campaign18_skip/armada2/keywords_skip.py',['CICADA_VOCAB','ESOTERIC_VOCAB','COMMON_WORDS','PUZZLE_VOCAB','SHORT_KEYS','build_keyword_list','tile_key','SCREEN_LEN','SCREEN_THR','SCREEN_BEAM','FULL_BEAM','CONF_THR','gate','attack_page_keyword_fast'],env)
words=env['build_keyword_list'];encode=env['eng_to_idx'];encrypt=env['encipher_keyskip'];text=env['idx_to_trans']
DENSE=np.full(26**4,Q.floor,np.float64)
for word,value in Q.d.items():
    code=0
    for c in word:code=code*26+ord(c)-65
    DENSE[code]=value
LETTERS=np.zeros((29,3),np.int64);LENGTHS=np.zeros(29,np.int64)
for i in range(29):
    s=gp.IDX_TO_TRANS[i]
    LENGTHS[i]=len(s)
    for j,c in enumerate(s):LETTERS[i,j]=ord(c)-65
@njit(cache=False)
def compiled(ct,key,sign,offset,length,width,dense,letters,lens,all_paths):
    need=offset+4*length+8
    if need>len(key):
        padded=np.zeros(need,np.int64);padded[:len(key)]=key;key=padded
    parent=np.zeros((length,width),np.int32);symbols=np.zeros((length,width),np.int16)
    scores=np.zeros(width,np.float64);ptr=np.zeros(width,np.int64);suffix=np.zeros(width,np.int64);latin=np.zeros(width,np.int64)
    first=(int(ct[0])+sign*key[offset])%29;symbols[0,0]=first;ptr[0]=offset;latin[0]=lens[first]
    code=0
    for j in range(lens[first]):code=(code*26+letters[first,j])%(26**3)
    suffix[0]=code;count=1;last=0
    for i in range(1,length):
        cap=count*4;ns=np.empty(cap,np.float64);npointer=np.empty(cap,np.int64);ncode=np.empty(cap,np.int64);nlatin=np.empty(cap,np.int64);nparent=np.empty(cap,np.int32);nrune=np.empty(cap,np.int16);used=0
        for b in range(count):
            for skip in range(4):
                accepted=ptr[b]+1+skip
                if accepted>=len(key):break
                rune=(int(ct[i])+sign*key[accepted])%29;valid=True
                for rejected in range(ptr[b]+1,accepted):
                    if (rune-sign*key[rejected])%29!=ct[i-1]:valid=False;break
                if not valid:continue
                tail=suffix[b];size=latin[b];delta=0.
                for j in range(lens[rune]):
                    full=tail*26+letters[rune,j]
                    if size>=3:delta+=dense[full]
                    tail=full%(26**3);size+=1
                ns[used]=scores[b]+delta;npointer[used]=accepted;ncode[used]=tail;nlatin[used]=size;nparent[used]=b;nrune[used]=rune;used+=1
        if used==0:break
        order=np.argsort(-ns[:used],kind='mergesort');count=min(width,used)
        for b in range(count):
            j=order[b];scores[b]=ns[j];ptr[b]=npointer[j];suffix[b]=ncode[j];latin[b]=nlatin[j];parent[i,b]=nparent[j];symbols[i,b]=nrune[j]
        last=i
    pathcount=count if all_paths else 1
    paths=np.empty((pathcount,last+1),np.int16)
    for b in range(pathcount):
        slot=b
        for i in range(last,-1,-1):paths[b,i]=symbols[i,slot];slot=parent[i,slot]
    return paths,scores[:count].copy(),ptr[:count].copy(),latin[:count].copy()
def beam(ct,key,sign,offset,length,width,terminal=False):
    out=compiled(np.asarray(ct,np.int64),np.asarray(key,np.int64),sign,offset,length,width,DENSE,LETTERS,LENGTHS,terminal)
    return out if terminal else out[0][0].astype(np.int64).tolist()
