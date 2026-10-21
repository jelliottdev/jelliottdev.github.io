"""Explicit encoder fixtures and transition rules for planted decoder controls.

These mechanisms are test fixtures, not proposed identifications of the LP cipher.
No source-repository modules are executed or imported.
"""
import hashlib
import random


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
