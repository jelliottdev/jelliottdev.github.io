"""Freeze pinned session17 Test8/9 period detectors before LP2 evaluation."""
import ast,hashlib,json,random,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
SRC=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
REV='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
SOURCE_PATH='tools/legacy/session17_clean_solve.py'
def blob(p):return subprocess.check_output(['git','-C',str(SRC),'show',REV+':'+p])
def sha(b):return hashlib.sha256(b).hexdigest()
script=blob(SOURCE_PATH);tree=ast.parse(script.decode('utf8'))
f8=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='test8_known_plaintext_attack')
f9=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='test9_kasiski_ioc')
def assigned(fn,name):
    found=[ast.literal_eval(x.value) for x in ast.walk(fn) if isinstance(x,ast.Assign)
           and any(isinstance(y,ast.Name) and y.id==name for y in x.targets)]
    assert len(found)==1,name
    return found[0]
candidates=assigned(f8,'LP_KNOWN_TEXTS')
period8=assigned(f8,'primes_to_test');period9=assigned(f9,'PRIMES_TO_TEST')
names=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA']
maps={v:i for i,v in enumerate(names)}
def source_digraph(text):
    t=text.upper();out=[];i=0
    dig={'TH':2,'EO':12,'NG':21,'EA':28,'AE':25,'IA':27,'OE':22}
    mono={'F':0,'U':1,'V':1,'O':3,'R':4,'C':5,'K':5,'G':6,'W':7,'H':8,'N':9,'I':10,'J':11,'P':13,
          'X':14,'S':15,'T':16,'B':17,'E':18,'M':19,'L':20,'D':23,'A':24,'Y':26}
    while i<len(t):
        if t[i:i+2] in dig:out.append(dig[t[i:i+2]]);i+=2
        else:
            if t[i] in mono:out.append(mono[t[i]])
            i+=1
    return out
candidate_rows=[{'name':name,'source_text_sha256':sha(text.encode('utf8')),
                 'gp_length':len(source_digraph(text)),'gp_sha256':sha(bytes(source_digraph(text)))}
                for name,text in candidates.items()]
pages=[]
for n in range(21,55):
    site=f'lp2-{n-17:02d}';sp=f'data/pages/{site}.json';sr=f'pages/page_{n:02d}/runes.txt'
    sb=(ROOT/sp).read_bytes();pages.append({'source_page':n,'site_page':site,'site_path':sp,
                                            'site_sha256':sha(sb),'rune_count':json.loads(sb)['rune_count'],
                                            'source_path':sr,'source_sha256':sha(blob(sr))})
key_rng=random.Random(71313);key=[key_rng.randrange(29) for _ in range(13)]
plan={'schema':'wulfic-session17-period-detectors-plan-v1',
      'timing':'Retrospective exact source detectors; source byte hashes, targets, thresholds, planted period and whole-scan controls frozen before LP2 results.',
      'source_revision':REV,'source_script':SOURCE_PATH,'source_script_sha256':sha(script),
      'source_url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/'+REV+'/'+SOURCE_PATH,
      'pages':pages,'test8_source_pages':list(range(21,35)),'test9_source_pages':list(range(21,55)),
      'test8_candidates':candidate_rows,'test8_periods':period8,'test9_periods':period9,
      'test8':'For each page and each of eight embedded texts, GP digraph conversion; offsets range(0,min(textGP_len+page_len,2000),max(1,page_len//20)); wrap candidate text; derive SUB and ADD keys as (cipher−plain)%29 and its negative; lag-match fraction for listed prime periods until p>=page_len//2, strictly >.25 reports. SUB/ADD period evidence is mathematically identical; preserve source rows, count one idea.',
      'test9':'For pages21–54, mean normalized 29×IoC across residue streams for listed prime periods p<=len(cipher)//3; source flag when best > whole-page 29×IoC ×1.3. Repeated-trigram first-repeat distances and all divisors are ancillary descriptive Kasiski counts without a success threshold.',
      'control':{'source_page_slot':21,'candidate':'LP1_CH1_P03','candidate_offset':0,
                 'cipher_length':'source page21 rune length','key_period':13,'key_values':key,
                 'construction':'cipher_i=(source candidate GP_i+key_i mod period)%29; candidate GP wraps per source Test8; all other source-page slots seeded uniform GP29 at original lengths',
                 'seed':71314,'requirements':'Test8 source known-plaintext candidate must report planted period13 at >.25; Test9 on planted page must flag and rank period13 first by split IoC. Check Kasiski descriptive support separately; no decoder is claimed.'},
      'null':{'trials':49,'seed':20261027,'method':'one independent within-page shuffle of each of the 34 original source pages per trial, shared by both detectors; rerun complete Test8 14-page candidate/offset/period search and Test9 34-page period scan; retain whole-grid maxima for each detector'},
      'source_overlap':'lp2-31-periodic-ioc is one page, periods2–20 and pooled IoC; this source uses mean column IoC and all declared pages/prime periods. Other crib-period records use different selection/crib rules.',
      'exclusions':'Nonprime periods, interrupted/restarted clocks, alternate candidate readings/encodings, other page groups, and a general claim that absence of a period peak excludes a cipher.'}
H.mkdir(parents=True,exist_ok=True)
(H/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
print(H/'plan.json')
