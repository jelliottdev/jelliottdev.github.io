"""Experimental source-equivalent representation of skipdecode.beam_decode.

Only the representation of a beam hypothesis changes. Branch order, key reads,
score additions, stable tie pruning and final Q.score_norm remain source-defined.
Do not use in manuscript sweeps without separate review.
"""
from __future__ import annotations


def beam_decode(C, K, *, gp, Q, sign=-1, o=0, beam_w=400, max_skip=3):
    n = gp.N
    d, floor = Q.d, Q.floor
    if o + len(C) + max_skip * len(C) >= len(K):
        Kx = K + [0] * (len(C) * (max_skip + 1) + 8)
    else:
        Kx = K
    p0 = (C[0] + sign * Kx[o]) % n
    t0 = gp.IDX_TO_TRANS[p0]
    # node = (rune_index, previous_node); none of the full paths is copied
    first = (p0, None)
    # hypothesis = (score, accepted_key_index, Latin_suffix, node, prev_cipher)
    beams = [(0.0, o, t0[-3:], first, C[0])]
    for i in range(1, len(C)):
        ci = C[i]
        nxt = []
        for sc, pa, suffix, node, cprev in beams:
            for dsk in range(max_skip + 1):
                acc = pa + 1 + dsk
                if acc >= len(Kx):
                    break
                p = (ci + sign * Kx[acc]) % n
                ok = True
                for m in range(pa + 1, acc):
                    if (p - sign * Kx[m]) % n != cprev:
                        ok = False
                        break
                if not ok:
                    continue
                add = gp.IDX_TO_TRANS[p]
                delta = 0.0
                tail = suffix
                for ch in add:
                    if len(tail) >= 3:
                        delta += d.get(tail[-3:] + ch, floor)
                    tail = (tail + ch)[-3:]
                nsc = sc + delta
                nxt.append((nsc, acc, tail, (p, node), ci))
        if not nxt:
            break
        nxt.sort(key=lambda item:item[0], reverse=True)
        beams = nxt[:beam_w]
    best = max(beams, key=lambda item:item[0])
    path = []
    node = best[3]
    while node is not None:
        path.append(node[0])
        node = node[1]
    path.reverse()
    translit = ''.join(gp.IDX_TO_TRANS[p] for p in path)
    return {'score':Q.score_norm(translit), 'beam_score':best[0],
            'plain_idx':path, 'ptr_end':best[1], 'translit':translit}
