"""Maintain two source-owned known-key follow-ups using synthetic controls only."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import authored_finite_followups as authored
import browser_followups as fixed
import finite_followup_cards as finite
from research_questions import validate_research_questions


def specified(value):
    return {'status': 'specified', 'value': value}


def candidate(reset):
    plan = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json').read_bytes())
    keys = [key['indices'][phase:] + key['indices'][:phase]
            for key in plan['keys'] for phase in range(len(key['indices']))]
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve', 'unmapped': 'preserve',
                        'inputVersion': 'raw', 'evaluation': copy.deepcopy(fixed.LANGUAGE_CRITERION),
                        'searchBounds': {'kind': 'finite-settings', 'version': 1, 'parameters': [
                            {'operation': 0, 'name': 'key', 'values': keys},
                            {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}]}}.items():
        rules[name] = specified(value)
    card = {'version': 1, 'outcome': specified({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
            'method': specified({'operations': [{'id': 'repeating_key', 'reset': reset}]}),
            'scope': specified({'pages': plan['pages']}), 'rules': rules, 'unresolved': []}
    if reset == 'page':
        metadata = dict(identifier='known-keys-language-comparison', title='Compare existing output with language samples',
            question='Do the existing outputs from the two known keys resemble the maintained language samples?',
            scope_change='Keep all 42 original key, starting-place and direction combinations on LP2-00–55; compare their full outputs with language samples instead of checking nine fixed openings.',
            limitation='Language similarity is not a recovered reading. This comparison reuses existing outputs; it does not test new keys, reset rules or interruptions.',
            motivation='Two number patterns from earlier decoded passages have already been tried on these pages. Compare the saved output with language samples to look beyond the original test of its first 12 runes.')
    else:
        metadata = dict(identifier='known-keys-word-reset-language', title='Start the number pattern again at every word',
            question='Does restarting either known key at every visible word produce outputs resembling the maintained language samples?',
            scope_change='Use the same 42 key, starting-place and direction combinations and LP2-00–55 pages, but restart the repeating key at every visible word rather than every page.',
            limitation='A higher language score is a lead to inspect, not a translation. Here, each non-rune mark ends a word.',
            motivation='Earlier decoded passages used two repeating number patterns. Try those same patterns here, but start again at every word rather than continuing through the page.')
    return authored.construct_followup(ROOT, card=card, **metadata)


def recipes():
    return [candidate(reset) for reset in ('page', 'word')]


def questions():
    return [
        {'id': 'known-keys-language-comparison',
         'state': 'open', 'note': 'Compare the complete archived outputs with language samples. The original result only checked nine fixed openings; language similarity is not a recovered reading.',
         'records': [], 'followup': 'known-keys-language-comparison', 'protocol': {'id': 'finite-settings-output', 'version': 1}},
        {'id': 'known-keys-word-reset-language',
         'state': 'open', 'note': 'Keep the original two keys, all starting places, both directions and the same pages. Change only the key restart from each page to each visible word. No result for this extension is asserted.',
         'records': [], 'followup': 'known-keys-word-reset-language', 'protocol': {'id': 'finite-settings-output', 'version': 1}}
    ]


def historical_questions():
    # Exact previously published projection only. Keep its immutable source
    # bytes readable until versioned source retrieval permits migration.
    value = questions()
    value[0]['question'] = 'Do the existing outputs from the two known keys resemble the maintained language samples?'
    value[1]['question'] = 'Does restarting either known key at each visible word improve its resemblance to language samples?'
    return value


def build(write=False):
    path = ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json'
    record = json.loads(path.read_bytes())
    generated = recipes()
    identifiers = {r['id'] for r in generated}
    expected = copy.deepcopy(record)
    expected['browser_followups'] = [r for r in record['browser_followups'] if r['id'] not in identifiers] + generated
    expected['research_questions'] = questions()
    validate_research_questions(expected['research_questions'], expected, strict_authoring=True)
    historical = copy.deepcopy(expected)
    historical['research_questions'] = historical_questions()
    serialized = json.dumps(expected, ensure_ascii=False, separators=(',', ':')) + '\n'
    if max(len(path.read_bytes()), len(serialized.encode('utf-8'))) >= 512 * 1024:
        raise ValueError('Known-key record exceeds the runtime source bound')
    if write:
        path.write_text(serialized, encoding='utf-8', newline='\n')
    elif record != expected:
        if record == historical:
            return record
        raise ValueError('Known-key source follow-up declarations are stale')
    return expected


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    value = build(write=args.write)
    print(json.dumps({'recordId': value['id'], 'finiteFollowups': 2, 'programsPerFollowup': 42, 'targetExecutions': 0}))
