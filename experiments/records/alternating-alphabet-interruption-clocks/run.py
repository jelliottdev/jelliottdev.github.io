"""Two explicit alphabet/interruption clocks; finite page-opening census."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'


def transform(values, keys, phases, start, sign, policy, encrypt=False, trace=False):
    counters, active, output, steps = list(phases), start, [], []
    for value in values:
        before = counters.copy()
        key = keys[active][counters[active] % len(keys[active])]
        if encrypt:
            rank = (value - sign * key) % 29
            cipher = rank if active == 0 else 28 - rank
            plain = value
        else:
            cipher = value
            rank = cipher if active == 0 else 28 - cipher
            plain = (rank + sign * key) % 29
        output.append(cipher if encrypt else plain)
        marker = cipher == 0
        if not marker:
            counters[active] += 1
        next_active = active if marker and policy == 'both' else 1 - active
        if trace:
            steps.append({'cipher': cipher, 'plain': plain, 'alphabet': active,
                          'key_index': key, 'counter_before': before,
                          'marker': marker, 'next_alphabet': next_active})
        active = next_active
    return output, steps


def configurations(plan):
    original = [row['indices'] for row in plan['keys']]
    for order in (0, 1):
        keys = original if order == 0 else original[::-1]
        for policy, sign, start in itertools.product(('key-only', 'both'), (-1, 1), (0, 1)):
            for a, b in itertools.product(range(len(keys[0])), range(len(keys[1]))):
                yield keys, (a, b), start, sign, policy, order


def report():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    digest = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    assert digest(plan['source_plan']) == plan['source_plan_sha256']
    baseline = json.loads((ROOT / plan['source_plan']).read_text(encoding='utf-8'))
    assert all(plan[name] == baseline[name] for name in ('keys', 'openings', 'pages'))
    index_path = 'data/index.json'
    assert ''.join(row['rune'] for row in json.loads((ROOT / index_path).read_text(encoding='utf-8'))['alphabet']) == ALPHABET
    inputs = {plan['source_plan']: digest(plan['source_plan']),
              index_path: digest(index_path),
              (HERE / 'plan.json').relative_to(ROOT).as_posix(): digest((HERE / 'plan.json').relative_to(ROOT))}
    pages = []
    for name in plan['pages']:
        path = f'text/{name}.txt'
        inputs[path] = digest(path)
        text = (ROOT / path).read_text(encoding='utf-8')
        assert not {c for c in text if '\u16a0' <= c <= '\u16ff' and c not in ALPHABET}
        runes = [ALPHABET.index(c) for c in text if c in ALPHABET]
        if runes:
            assert len(runes) >= 12
            pages.append((name, runes[:12]))
    assert len(pages) == 55
    cribs = [row['indices'] for row in plan['openings']]
    results = {p: {'settings': 0, 'page_cases': 0, 'comparisons': 0,
                   'exact_matches': 0, 'max_prefix': 0} for p in ('key-only', 'both')}
    census = hashlib.sha256()
    controls = wrong_policy_changes = settings = 0
    best = []
    plant = [i % 29 for i in range(87)]
    forced = [4, 12, 0, 0, 8, 16, 21, 6, 17, 0, 23, 25]
    for keys, phases, start, sign, policy, order in configurations(plan):
        settings += 1
        row = results[policy]
        row['settings'] += 1
        encrypted, _ = transform(plant, keys, phases, start, sign, policy, True)
        decoded, _ = transform(encrypted, keys, phases, start, sign, policy)
        assert decoded == plant
        controls += 1
        forced_plain, forced_trace = transform(forced, keys, phases, start, sign, policy, trace=True)
        expected_alphabets = [(start + (i if policy == 'key-only' else sum(c != 0 for c in forced[:i]))) % 2
                              for i in range(len(forced))]
        for i, step in enumerate(forced_trace):
            expected = [phases[a] + sum(forced[j] != 0 and expected_alphabets[j] == a for j in range(i))
                        for a in (0, 1)]
            assert step['alphabet'] == expected_alphabets[i] and step['counter_before'] == expected
        reconstructed, _ = transform(forced_plain, keys, phases, start, sign, policy, True)
        assert reconstructed == forced
        other = 'both' if policy == 'key-only' else 'key-only'
        wrong, _ = transform(forced, keys, phases, start, sign, other)
        wrong_policy_changes += wrong != forced_plain
        for page, cipher in pages:
            plain, _ = transform(cipher, keys, phases, start, sign, policy)
            census.update(bytes(plain))
            row['page_cases'] += 1
            for crib in cribs:
                prefix = next((i for i, (a, b) in enumerate(zip(plain, crib)) if a != b), 12)
                row['comparisons'] += 1
                row['exact_matches'] += prefix == 12
                row['max_prefix'] = max(row['max_prefix'], prefix)
                if prefix >= 4 and len(best) < 20:
                    best.append({'page': page, 'policy': policy, 'key_assignment': order,
                                 'phases': phases, 'start': start, 'sign': sign, 'prefix': prefix,
                                 'plain': plain})
    keys = [r['indices'] for r in plan['keys']]
    traces = {policy: transform(forced, keys, (0, 0), 0, -1, policy, trace=True)[1]
              for policy in results}
    assert settings == 1664 and controls == 1664 and wrong_policy_changes > 0
    return {'schema': 'liberpedia-two-clock-result-v1', 'input_sha256': inputs,
            'settings': settings, 'pages_compared': len(pages), 'runeless_page': 'lp2-50',
            'by_policy': results, 'head_census_sha256': census.hexdigest(),
            'controls': {'roundtrips': controls, 'runes_each': len(plant),
                         'forced_marker_roundtrips': settings,
                         'wrong_policy_changes': wrong_policy_changes},
            'illustrative_first_twenty_prefixes_at_least_four': best,
            'clock_example': traces}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    else:
        (HERE / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                                         encoding='utf-8', newline='\n')
    print(result['settings'], 'settings;', sum(r['exact_matches'] for r in result['by_policy'].values()), 'exact matches')
