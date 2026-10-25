"""Validate authored question links without inferring experimental coverage.

An editor's tested/open state applies only to the written question. These links
do not close a method family, establish equivalence, or execute any experiment.
"""
import re


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


def validate_research_questions(value, record):
    """Validate local shape and owned recipe names; never read or write files."""
    require(isinstance(value, list) and 1 <= len(value) <= 12, 'expected 1..12 questions')
    seen = set()
    linked = set()
    recipes = {recipe['id'] for recipe in record.get('browser_followups', [])}
    for question in value:
        require(isinstance(question, dict), 'question must be an object')
        require(set(question) in (FIELDS, FIELDS | {'followup'}), 'unexpected question fields')
        identifier = question['id']
        require(slug(identifier, 100) and identifier not in seen, 'invalid or duplicate question id')
        seen.add(identifier)
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


def validate_research_question_refs(records, by_id):
    """Resolve all links after loading records, before any generated file writes."""
    for record in records:
        for question in record.get('research_questions', []):
            require(all(reference in by_id and reference != record['id']
                        for reference in question['records']),
                    record['id'] + '/' + question['id'] + ': links must name other published records')
