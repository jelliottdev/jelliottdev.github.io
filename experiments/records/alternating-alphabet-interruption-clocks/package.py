"""Package the frozen clock census with its exact local dependencies."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
identifier = HERE.name
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
baseline = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json').read_text(encoding='utf-8'))
scope = {
    'pages': [f'lp2-{n:02d}' for n in range(56) if n != 50],
    'representation': 'First twelve GP29 runes, including headings, of LP2-00–55; omit runeless LP2-50. Page-local state. Other characters do not advance it.',
    'procedure': 'Alternate ordinary/reversed cipher alphabets, each with its own known repeating key. Decode F normally but hold the selected key position there. Compare always-toggling versus F-paused alphabet clocks; compare each head with nine fixed twelve-rune known-reading openings.',
    'parameters': '2 key assignments × 104 phase pairs × 2 first alphabets × 2 signs × 2 clock policies = 1,664 settings; 55 pages; 823,680 exact comparisons. 1,664 roundtrips on 87 prescribed runes plus 1,664 forced-marker controls.',
    'exclusions': 'Other keys, cipher alphabet permutations, literal/removed F, other interruption runes, word resets, additional layers, noninitial starts and unknown plaintext openings. No historical exact-method replay is claimed.'}
def artifact(name):
    path = HERE / name
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

inputs = [{'path': p, 'sha256': h} for p, h in sorted(result['input_sha256'].items())]
inputs += [artifact(name) for name in ('run.py', 'check.py', 'plot.py', 'package.py', 'article.md')]
record = {
    'id': identifier, 'status': 'published',
    'title': 'Alternating alphabets with two interruption clocks',
    'question': 'Do two known keys, alternating GP/reversed-GP cipher alphabets and either of two ciphertext-F pause rules recover a declared page opening?',
    'reader_question': 'Could F pause the key, the alphabet, or both?',
    'summary': 'Neither F-clock rule recovered a declared twelve-rune opening in 55 LP2 pages.',
    'finding': 'No exact opening among 823,680 comparisons across 1,664 settings. The longest shared prefix was three runes. All state-machine roundtrips and the independent closed-form census pass.',
    'reader_finding': 'Neither rule revealed a known opening. Pausing just the key or both clocks was tested with both known keys, every starting phase, and both arithmetic directions.',
    'reader_limit': 'This checks two specified ciphers and nine predicted beginnings. Other keys, interruption rules and unknown openings remain possible.',
    'limitations': scope['exclusions'],
    'next_steps': 'Require a new key, state transition or independently predicted continuation before extending this baseline.',
    'tags': ['alternating alphabets', 'two clocks', 'F interruption', 'Vigenere', 'known keys', 'page openings'],
    'family': baseline['family'],
    'variant': {'label': 'Alternating cipher alphabets and F-paused clocks',
                'changes': [{'field': k, 'before': baseline['scope'][k], 'after': v,
                             'reason': 'Define and test the proposed two-clock extension without treating the uninterrupted baseline as coverage.'}
                            for k, v in scope.items() if baseline['scope'][k] != v]},
    'scope': scope, 'outcome': 'not-supported',
    'reproduction': {'command': f'python experiments/records/{identifier}/run.py --check',
                     'environment': 'Python 3.9 or later, standard library only. Run check.py for the independent census and plot.py --check for the figure.',
                     'script': artifact('run.py')['path'], 'script_sha256': artifact('run.py')['sha256'],
                     'inputs': inputs, 'outputs': [artifact('results.json'), artifact('clocks.svg')]},
    'review': {'reviewer': 'Independent closed-form clock census and all-setting roundtrip controls',
               'retested_on': '2026-10-23', 'kind': 'computational', 'human_review': 'pending'},
    'sources': baseline['sources'],
    'related': ['lp2-known-vigenere-keys', 'four-phase-ioc', 'grouped-key-advance-openings'],
    'visuals': [{'path': artifact('clocks.svg')['path'],
                 'caption': 'F pauses the selected key in both versions. The two rows show whether the cipher alphabet switches anyway or pauses with it.'}]}
(HERE / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
