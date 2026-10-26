"""Validate authored question links without inferring experimental coverage.

An editor's tested/open state applies only to the written question. These links
do not close a method family, establish equivalence, or execute any experiment.
"""
import re
import copy


SLUG = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*')
FIELDS = {'id', 'question', 'state', 'note', 'records'}


def require(condition, message):
    if not condition:
        raise ValueError('research_questions: ' + message)


def slug(value, maximum=None):
    return (isinstance(value, str) and SLUG.fullmatch(value) is not None
            and (maximum is None or len(value) <= maximum))


def prose(value, maximum, label):
    require(isinstance(value, str) and value == value.strip() and value
            and len(value.encode('utf-16-le', errors='surrogatepass')) // 2 <= maximum
            and not re.search(r'[<>\x00-\x1f\x7f\[\]`*\\\u2028\u2029\ud800-\udfff]', value),
            label + ': expected bounded plain text')


def protocol_reference(question, record):
    """Resolve a declared definition; never derive a live answer from editorial state."""
    if 'protocol' not in question:
        return None
    protocol = question['protocol']
    require(isinstance(protocol, dict) and set(protocol) == {'id', 'version'}
            and type(protocol['version']) is int and protocol['version'] == 1,
            'invalid maintained protocol reference')
    if protocol['id'] == 'deor-warning-opening':
        require('followup' not in question, 'DEOR definition cannot inherit another follow-up scope')
        return {'id': protocol['id'], 'version': 1, 'familyId': 'deor-feedback-v1'}
    require(protocol['id'] in ('word-boundary-sensitivity', 'fixed-program-prefix', 'finite-settings-output') and 'followup' in question,
            'unknown protocol or missing owned boundary follow-up')
    require(isinstance(record.get('browser_followups'), list)
            and all(isinstance(recipe, dict) for recipe in record['browser_followups']),
            'invalid owned boundary follow-ups')
    owned = [recipe for recipe in record.get('browser_followups', [])
             if recipe.get('id') == question['followup']]
    require(len(owned) == 1, 'boundary protocol needs one owned follow-up')
    recipe = owned[0]
    card, inputs = recipe.get('card', {}), recipe.get('inputs', {})
    require(isinstance(card, dict), 'invalid boundary card')
    method, rules, scope = card.get('method', {}), card.get('rules', {}), card.get('scope', {})
    require(all(isinstance(value, dict) for value in (method, rules, scope)), 'invalid boundary card fields')
    evaluation = rules.get('evaluation', {})
    require(isinstance(evaluation, dict), 'invalid boundary evaluation')
    criterion = evaluation.get('value', {})
    if protocol['id'] == 'finite-settings-output':
        from finite_followup_cards import compile_card
        require(recipe.get('kind') == 'finite-settings', 'finite protocol needs an owned finite recipe')
        try:
            expanded = compile_card(card)
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError('research_questions: incompatible finite-settings recipe') from error
        compiled = expanded['variants'][0]['compiled']
        require(isinstance(inputs, dict) and set(inputs) == {'version', 'alphabet_sha256', 'pages'}
                and inputs['version'] == compiled['inputVersion']
                and isinstance(inputs['alphabet_sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', inputs['alphabet_sha256'])
                and isinstance(inputs['pages'], list) and len(inputs['pages']) == len(compiled['pages'])
                and all(isinstance(page, dict) and set(page) == {'id', 'text_sha256'}
                        and page['id'] == identifier and isinstance(page['text_sha256'], str)
                        and re.fullmatch(r'[a-f0-9]{64}', page['text_sha256'])
                        for page, identifier in zip(inputs['pages'], compiled['pages'])),
                'finite scope must match exact follow-up pins')
        return {'id': protocol['id'], 'version': 1, 'followupId': recipe['id'], 'inputs': copy.deepcopy(inputs)}
    require('kind' not in recipe, 'legacy fixed protocol cannot accept a finite or unknown recipe kind')
    if protocol['id'] == 'fixed-program-prefix':
        # Publication uses the existing maintained compiler. No second method
        # implementation or inferred program is introduced for question views.
        from browser_followups import compile_card
        try:
            compiled = compile_card(card)
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError('research_questions: incompatible fixed-prefix recipe') from error
        require(isinstance(criterion, dict) and set(criterion) == {'kind', 'values'}
                and criterion['kind'] == 'exact-prefix' and isinstance(criterion['values'], list)
                and 1 <= len(criterion['values']) <= 256
                and all(type(n) is int and 0 <= n <= 28 for n in criterion['values'])
                and compiled['criterion'] == criterion, 'invalid fixed-prefix criterion')
        require(isinstance(inputs, dict) and set(inputs) == {'version', 'alphabet_sha256', 'pages'}
                and inputs['version'] == compiled['inputVersion']
                and isinstance(inputs['alphabet_sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', inputs['alphabet_sha256'])
                and isinstance(inputs['pages'], list) and len(inputs['pages']) == len(compiled['pages'])
                and all(isinstance(page, dict) and set(page) == {'id', 'text_sha256'}
                        and page['id'] == identifier and isinstance(page['text_sha256'], str)
                        and re.fullmatch(r'[a-f0-9]{64}', page['text_sha256'])
                        for page, identifier in zip(inputs['pages'], compiled['pages'])),
                'fixed-prefix scope must match exact follow-up pins')
        return {'id': protocol['id'], 'version': 1, 'followupId': recipe['id'], 'inputs': copy.deepcopy(inputs)}
    require(type(card.get('version')) is int and card.get('version') == 1 and card.get('unresolved') == []
            and method.get('status') == 'specified'
            and isinstance(method.get('value'), dict) and set(method['value']) == {'operations'}
            and isinstance(method['value']['operations'], list) and len(method['value']['operations']) == 1
            and evaluation.get('status') == 'specified'
            and isinstance(criterion, dict) and set(criterion) == {'kind', 'lag', 'a', 'b', 'boundaries'}
            and criterion['kind'] == 'word-affine-count'
            and type(criterion['lag']) is int and 1 <= criterion['lag'] <= 12
            and all(type(criterion[k]) is int and 0 <= criterion[k] <= 28 for k in ('a', 'b'))
            and criterion['boundaries'] in ('non-rune', 'hyphen-period'),
            'incompatible boundary measurement')
    operation = method['value']['operations'][0]
    require(isinstance(operation, dict)
            and set(operation) in ({'id', 'lag', 'a', 'b', 'boundaries'}, {'id', 'label', 'lag', 'a', 'b', 'boundaries'})
            and operation['id'] == 'word_affine_count'
            and ('label' not in operation or operation['label'] == 'Within-word affine pair count')
            and all(type(operation[k]) is type(criterion[k]) and operation[k] == criterion[k]
                    for k in ('lag', 'a', 'b', 'boundaries')), 'boundary operation/evaluation disagree')
    require(isinstance(inputs, dict) and set(inputs) == {'version', 'alphabet_sha256', 'pages'}
            and inputs['version'] in ('raw', 'reviewed')
            and isinstance(inputs['alphabet_sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', inputs['alphabet_sha256'])
            and isinstance(inputs['pages'], list) and 1 <= len(inputs['pages']) <= 75
            and all(isinstance(page, dict) and set(page) == {'id', 'text_sha256'}
                    and isinstance(page['id'], str) and re.fullmatch(r'lp[12]-\d{2}', page['id'])
                    and isinstance(page['text_sha256'], str) and re.fullmatch(r'[a-f0-9]{64}', page['text_sha256'])
                    for page in inputs['pages'])
            and len({page['id'] for page in inputs['pages']}) == len(inputs['pages'])
            and scope.get('status') == 'specified' and isinstance(scope.get('value'), dict)
            and scope['value'] == {'pages': [page['id'] for page in inputs['pages']]},
            'boundary scope must match exact follow-up pins')
    for key, value in {'representation': 'GP29', 'wordBoundaries': 'preserve',
                       'unmapped': 'preserve', 'inputVersion': inputs['version']}.items():
        require(rules.get(key) == {'status': 'specified', 'value': value}, 'incompatible boundary input rule')
    for key in ('boundaryMode', 'reset', 'initialState', 'searchBounds', 'searchProtocol', 'exceptionalCases'):
        require(rules.get(key) == {'status': 'not_applicable'}, 'incompatible boundary extra rule')
    return {'id': protocol['id'], 'version': 1, 'followupId': recipe['id'],
            'parameters': {key: criterion[key] for key in ('lag', 'a', 'b')}, 'inputs': copy.deepcopy(inputs)}


def validate_research_questions(value, record, *, strict_authoring=False):
    """Validate local shape and owned recipe names; never read or write files."""
    require(isinstance(value, list) and 1 <= len(value) <= 12, 'expected 1..12 questions')
    seen = set()
    linked = set()
    recipes = {recipe['id'] for recipe in record.get('browser_followups', [])}
    for question in value:
        require(isinstance(question, dict), 'question must be an object')
        require(FIELDS - {'question'} <= set(question) <= FIELDS | {'followup', 'protocol'}, 'unexpected question fields')
        identifier = question['id']
        require(slug(identifier, 100) and identifier not in seen, 'invalid or duplicate question id')
        seen.add(identifier)
        if 'question' in question:
            prose(question['question'], 300, identifier + '.question')
        prose(question['note'], 700, identifier + '.note')
        state = question['state']
        require(state in ('tested', 'open'), identifier + ': invalid state')
        references = question['records']
        require(isinstance(references, list) and len(references) <= 12
                and all(slug(reference, 100) for reference in references),
                identifier + ': records must be record IDs')
        require(len(set(references)) == len(references), identifier + ': duplicate record link')
        require(record['id'] not in references, identifier + ': self reference')
        require(state != 'tested' or references, identifier + ': tested question needs a record link')
        if 'followup' in question:
            require(slug(question['followup'], 100)
                    and question['followup'] in recipes and question['followup'] not in linked,
                    identifier + ': followup must name one unique owned recipe')
            linked.add(question['followup'])
        resolved = protocol_reference(question, record)
        canonical = None
        if resolved and 'followupId' in resolved:
            owned = [r for r in record.get('browser_followups', []) if r.get('id') == resolved['followupId']]
            require(len(owned) == 1, identifier + ': question needs one owned recipe')
            canonical = owned[0].get('question')
            prose(canonical, 1200, identifier + '.followup.question')
        require(canonical is not None or 'question' in question,
                identifier + ': standalone question needs authored wording')
        if strict_authoring and canonical is not None and 'question' in question:
            require(question['question'] == canonical, identifier + ': duplicated question conflicts with followup')


def validate_research_question_refs(records, by_id):
    """Resolve all links after loading records, before any generated file writes."""
    for record in records:
        for question in record.get('research_questions', []):
            require(all(reference in by_id and reference != record['id']
                        for reference in question['records']),
                    record['id'] + '/' + question['id'] + ': links must name other published records')
