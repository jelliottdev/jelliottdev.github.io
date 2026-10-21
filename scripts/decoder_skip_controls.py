"""Explicit encoder fixtures and transition rules for planted decoder controls.

These mechanisms are test fixtures, not proposed identifications of the LP cipher.
No source-repository modules are executed or imported.
"""
import hashlib
import random
import math


def key_fixture(seed, repetition=1, slots=10000):
    assert repetition in (1,4) and slots > 0
    prefix = f'liberpedia-decoder-control:{seed}'.encode('ascii')
    values = []; counter = 0
    while len(values) < slots:
        block = hashlib.sha256(prefix + counter.to_bytes(4,'big')).digest()
        for byte in block:
            values.extend([byte % 29] * repetition)
        counter += 1
    return values[:slots]


def encode(plain, key, mechanism, seed=0, modulus=29, *, draws=None):
    assert mechanism in ('rigid','skip','rewrite','drift-skip')
    assert modulus >= 2 and plain
    assert all(type(v) is int and 0 <= v < modulus for v in plain + key)
    rng = draws if draws is not None else random.Random(3301+seed)
    ciphertext = []; trace = []; pointer = 0
    for position,p in enumerate(plain):
        begin = pointer; rejected = []; decisions = []; drift = []
        if mechanism == 'drift-skip' and position == len(plain)//2:
            if pointer >= len(key):raise ValueError('Key exhausted during unrelated advance')
            drift.append(pointer); pointer += 1
        rewritten = False
        while True:
            if pointer >= len(key):raise ValueError('Key exhausted; padding is forbidden')
            proposed = (p+key[pointer]) % modulus
            collision = bool(ciphertext) and proposed == ciphertext[-1]
            reject = False
            if collision and mechanism != 'rigid':
                draw = rng.randrange(100)
                decisions.append({'key_slot':pointer,'draw':draw})
                reject = draw < 83
            if reject and mechanism in ('skip','drift-skip'):
                rejected.append(pointer); pointer += 1
                continue
            if reject and mechanism == 'rewrite':
                rewritten = True
            c = (proposed+int(rewritten)) % modulus
            ciphertext.append(c)
            trace.append({'position':position,'plain':p,'pointer_before':begin,
                          'unrelated_slots':drift,'rejected_slots':rejected,'decisions':decisions,
                          'accepted_slot':pointer,'proposed':proposed,'rewritten':rewritten,'cipher':c})
            pointer += 1
            break
    return ciphertext,trace


def transitions(cipher, previous_cipher, key, previous_slot, maximum_skip, modulus=29):
    """Enumerate accepted slot and plaintext; previous_slot=None means first rune."""
    assert maximum_skip >= 0
    if previous_slot is None:
        if not key:raise ValueError('Empty key')
        return [(0,(cipher-key[0]) % modulus)]
    out = []
    for skip in range(maximum_skip+1):
        accepted = previous_slot+1+skip
        if accepted >= len(key):break
        plain = (cipher-key[accepted]) % modulus
        if all((plain+key[k]) % modulus == previous_cipher for k in range(previous_slot+1,accepted)):
            out.append((accepted,plain))
    return out


def true_path_failure(ciphertext, plain, trace, key, maximum_skip, modulus=29):
    previous = None
    for i,(c,p,t) in enumerate(zip(ciphertext,plain,trace,strict=True)):
        choices = transitions(c,ciphertext[i-1] if i else None,key,previous,maximum_skip,modulus)
        if (t['accepted_slot'],p) not in choices:return i
        previous = t['accepted_slot']
    return None


def load_model(path):
    counts={}
    for line in path.read_text(encoding='ascii').splitlines():
        gram,raw=line.split(); count=int(raw)
        assert len(gram)==4 and all('A'<=c<='Z' for c in gram) and gram not in counts and count>0
        counts[gram]=count
    total=sum(counts.values()); logtotal=math.log10(total)
    return {g:math.log10(n)-logtotal for g,n in counts.items()},math.log10(.01)-logtotal


def append_score(score, text, addition, model, floor):
    tail=text[-3:]+addition
    for i in range(len(tail)-3):score+=model.get(tail[i:i+4],floor)
    return score


def beam_decode(ciphertext,key,width,maximum_skip,labels,model,floor,plain,trace,modulus=29):
    """Fixed-width beam, cumulative score; track truth only for diagnostics."""
    assert width>0 and ciphertext
    # No candidate selection reads the known plaintext or encoder trace.
    beams=[(0.0,(),(),'')]; first_pruned=None
    invalid=true_path_failure(ciphertext,plain,trace,key,maximum_skip,modulus)
    truth_slots=tuple(t['accepted_slot'] for t in trace); truth_plain=tuple(plain)
    for i,c in enumerate(ciphertext):
        candidates=[]
        for score,slots,indices,text in beams:
            for slot,p in transitions(c,ciphertext[i-1] if i else None,key,slots[-1] if slots else None,maximum_skip,modulus):
                add=labels[p]
                candidates.append((append_score(score,text,add,model,floor),slots+(slot,),indices+(p,),text+add))
        if not candidates:raise ValueError('No complete decoder path; no partial answer permitted')
        candidates.sort(key=lambda v:(-v[0],v[1],v[2]))
        beams=candidates[:width]
        if first_pruned is None and (invalid is None or i<invalid):
            if not any(s==truth_slots[:i+1] and p==truth_plain[:i+1] for _,s,p,_ in beams):
                first_pruned=i
    score,slots,indices,text=beams[0]
    return {'indices':list(indices),'slots':list(slots),'transliteration':text,
            'cumulative_score':score,'normalized_score':score/(len(text)-3) if len(text)>3 else None,
            'first_invalid_truth_step':invalid,'first_pruned_truth_step':first_pruned}


def rigid_decode(ciphertext,key,labels,model,floor,plain,trace,modulus=29):
    if len(key)<len(ciphertext):raise ValueError('Key exhausted')
    indices=[(c-key[i])%modulus for i,c in enumerate(ciphertext)]
    text=''.join(labels[p] for p in indices)
    score=0.0
    for i in range(len(text)-3):score+=model.get(text[i:i+4],floor)
    return {'indices':indices,'slots':list(range(len(indices))),'transliteration':text,
            'cumulative_score':score,'normalized_score':score/(len(text)-3) if len(text)>3 else None,
            'first_invalid_truth_step':true_path_failure(ciphertext,plain,trace,key,0,modulus),
            'first_pruned_truth_step':None}
