"""Independent finite beam, whole-survivor rescoring and grid recount."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def independent_model():
    raw = {}
    for line in (HERE / 'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        word, count = line.split()
        raw[word] = int(count)
    total = sum(raw.values())
    return {word: math.log10(count) - math.log10(total) for word, count in raw.items()}, math.log10(.01) - math.log10(total)


MODEL, FLOOR = independent_model()


def score(text):
    return sum(MODEL.get(text[i:i+4], FLOOR) for i in range(len(text)-3)) / (len(text)-3)


def decode(cipher, key, sign, offset, length, width, spellings):
    # Stable ordering and cumulative character-quadgrams are historical behavior.
    p0 = (cipher[0] + sign * key[offset]) % 29
    states = [(0., offset, (p0,), spellings[p0], (offset,))]
    for i in range(1, length):
        candidates = []
        for cumulative, pointer, plain, text, used in states:
            for skipped in range(4):
                position = pointer + 1 + skipped
                if position >= len(key):
                    break
                plain_value = (cipher[i] + sign * key[position]) % 29
                if any((plain_value - sign * key[j]) % 29 != cipher[i-1] for j in range(pointer+1, position)):
                    continue
                extended = text + spellings[plain_value]
                delta = sum(MODEL.get(extended[end-4:end], FLOOR)
                            for end in range(max(4, len(text)+1), len(extended)+1))
                candidates.append((cumulative + delta, position, plain + (plain_value,), extended, used + (position,)))
        if not candidates:
            break
        candidates.sort(key=lambda item: item[0], reverse=True)
        states = candidates[:width]
    winner = max(states, key=lambda item: item[0])
    return list(winner[2]), winner[3], list(winner[4])


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert run.sha(ROOT / item['path']) == item['sha256'], item['path']
    report = json.loads((HERE / 'results.json').read_text(encoding='utf8'))
    assert report['plan_sha256'] == run.sha(HERE / 'plan.json')
    assert report['cases_sha256'] == run.sha(HERE / 'cases.json')
    rows = json.loads((HERE / 'cases.json').read_text(encoding='utf8'))
    source, _, _, streams, pages = run.load()
    page_map = dict(zip(plan['page_ids'], pages))
    keys = {x['name']: x['key'] for x in streams}
    expected = {(name, page, sign, atbash, offset) for name in keys for page in page_map
                for sign in (-1, 1) for atbash in (0, 1) for offset in range(5)}
    actual = [(r['stream'], r['page'], r['sign'], r['atbash'], r['offset']) for r in rows]
    assert len(rows) == len(set(actual)) == 23100 and set(actual) == expected
    assert all(r['selected_full'] == (r['screen_score'] > -6.5) for r in rows)
    full = [r for r in rows if r['selected_full']]
    assert len(full) == report['full_confirmations']
    assert sum(r['full_score'] > -5.5 for r in full) == report['source_gate_passes']
    checks = [(r, True) for r in full]
    checks += [(r, False) for r in sorted(rows, key=lambda r: r['screen_score'], reverse=True)[:10]]
    observations = []
    for r, whole in checks:
        cipher = [(28-c if r['atbash'] else c) for c in page_map[r['page']]]
        plain, text, used = decode(cipher, keys[r['stream']], r['sign'], r['offset'],
                                   len(cipher) if whole else min(50, len(cipher)), 300 if whole else 60,
                                   source.gp.IDX_TO_TRANS)
        assert hashlib.sha256(bytes(plain)).hexdigest() == r['full_sha256' if whole else 'screen_sha256']
        assert abs(score(text) - r['full_score' if whole else 'screen_score']) < 1e-10
        if whole:
            assert plain == r['full_indices'] and len(plain) == len(cipher)
            assert r['source_gate_pass'] == (score(text) > -5.5)
        observations.append({'setting': {k:r[k] for k in ['stream','page','sign','atbash','offset']},
                             'whole_page':whole, 'independent_score':score(text),
                             'first12_indices':plain[:12], 'first12_key_positions':used[:12]})
    # Whole finite arrays, not labels, determine phase aliases.
    phase = {}
    for name, key in keys.items():
        groups = {}
        for offset in range(5):
            groups.setdefault(bytes(key[offset:offset+1108]), []).append(offset)
        dup = [g for g in groups.values() if len(g)>1]
        if dup:
            phase[name] = dup
    assert phase == {'magic_sq_rowsums': [[0,1,2,3,4]], '3301_decimal': [[0,4]]}
    for r in rows:
        if r['stream'] == 'magic_sq_rowsums' or (r['stream'] == '3301_decimal' and r['offset'] == 4):
            twin = next(x for x in rows if x['stream'] == r['stream'] and x['page'] == r['page']
                        and x['sign'] == r['sign'] and x['atbash'] == r['atbash'] and x['offset'] == 0)
            assert twin['screen_sha256'] == r['screen_sha256']
            assert twin['screen_score'] == r['screen_score']
    assert max(rows,key=lambda r:r['screen_score']) == report['best_screen']
    assert (max(full,key=lambda r:r['full_score']) if full else None) == report['best_full']
    terminal_checks = 0
    if (HERE / 'terminal-audit.json').exists():
        terminal = json.loads((HERE / 'terminal-audit.json').read_text(encoding='utf8'))
        assert terminal['terminal_plan_sha256'] == run.sha(HERE / 'terminal-plan.json')
        for r in terminal['rows']:
            cipher = [(28-c if r['atbash'] else c) for c in page_map[r['page']]]
            plain = r['best_terminal_indices']
            key = keys[r['stream']]
            text = ''.join(source.gp.IDX_TO_TRANS[p] for p in plain)
            assert len(plain) == len(cipher)
            assert abs(score(text)-r['best_normalized_terminal_score']) < 1e-10
            assert hashlib.sha256(bytes(plain)).hexdigest() == r['best_terminal_sha256']
            # Independent existence check for a legal key-pointer path yielding this witness.
            pointers = {r['offset']}
            assert (cipher[0]+r['sign']*key[r['offset']]) % 29 == plain[0]
            for i in range(1,len(cipher)):
                next_pointers = set()
                for pointer in pointers:
                    for skipped in range(4):
                        position = pointer+1+skipped
                        if position >= len(key):
                            continue
                        if (cipher[i]+r['sign']*key[position]) % 29 != plain[i]:
                            continue
                        if all((plain[i]-r['sign']*key[j]) % 29 == cipher[i-1] for j in range(pointer+1,position)):
                            next_pointers.add(position)
                pointers = next_pointers
                assert pointers
            assert r['terminal_gate_pass'] == (score(text)>-5.5)
            terminal_checks += 1
        assert terminal_checks == len(full)
        assert terminal['terminal_gate_passes'] == sum(x['terminal_gate_pass'] for x in terminal['rows'])
    receipt = {'schema':'artifact-stream-independent-check-v1','settings_recounted':23100,
               'all_full_survivors_independently_decoded':len(full),'best_short_outputs_independently_decoded':10,
               'whole_survivor_and_best_hashes_scores_match':True,'phase_aliases':phase,
               'nominal_phase_labels':105,'distinct_per_stream_phase_arrays':100,
               'source_gate_passes':report['source_gate_passes'],'checks':observations,
               'post_target_terminal_witnesses_independently_rescored_and_admissible':terminal_checks,
               'limits':'Independent implementation confirms source-selected outputs, not their English validity or global detection power.'}
    (HERE / 'independent-check.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='checks'},indent=2))


if __name__ == '__main__':
    main()
