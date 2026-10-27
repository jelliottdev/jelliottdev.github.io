"""Compile one authored experiment into the stable public record contract.

V2 record.json is the only authored content file. article.md and public aliases
are derived views; this module never writes files or executes experiments.
"""
import copy
import datetime
import json
import re
import unicodedata

SCHEMA = 'liberpedia-experiment-v2'
DERIVED = {'summary', 'finding', 'limitations', 'next_steps', 'reader_finding',
           'reader_limit', 'reader_question', 'article', 'article_path', 'reader_sections',
           'record_type', 'method_topics', 'script_sha256', 'article_links'}


def validate_published_programs(record):
    """Declare retained outputs; the publication builder verifies their contents.

    A declaration never supplies or infers a task, method, result or source hash.
    The retained output's existing reproduction pin is the only source binding.
    """
    if 'published_programs' not in record:
        return
    declarations = record['published_programs']
    identifier = record.get('id')
    if (not isinstance(identifier, str)
            or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier)
            or not isinstance(declarations, list) or not 1 <= len(declarations) <= 32):
        raise ValueError('published_programs needs 1–32 declarations on a named record')
    reproduction = record.get('reproduction')
    outputs = reproduction.get('outputs') if isinstance(reproduction, dict) else None
    if not isinstance(outputs, list):
        raise ValueError('published_programs needs pinned reproduction.outputs')
    ids, paths = set(), set()
    prefix = 'experiments/records/' + identifier + '/'
    for item in declarations:
        if not isinstance(item, dict) or set(item) != {'id', 'output', 'checked_at'}:
            raise ValueError('published_programs supports id, output and checked_at only')
        name, path, checked_at = item['id'], item['output'], item['checked_at']
        if (not isinstance(name, str) or len(name) > 80
                or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', name)
                or name in ids):
            raise ValueError('published_programs needs distinct short program IDs')
        if (not isinstance(path, str) or len(path) > 300
                or not path.startswith(prefix) or not path.endswith('.json')
                or not re.fullmatch(r'[a-zA-Z0-9_./-]+', path)
                or any(part in ('', '.', '..') for part in path.split('/'))
                or path in paths or path in (prefix + 'record.json', prefix + 'article.json')):
            raise ValueError('published_programs needs distinct record-local JSON outputs')
        pins = [entry for entry in outputs if isinstance(entry, dict) and entry.get('path') == path]
        if (len(pins) != 1 or not isinstance(pins[0].get('sha256'), str)
                or not re.fullmatch(r'[a-f0-9]{64}', pins[0]['sha256'])):
            raise ValueError('published_programs output needs exactly one reproduction output pin')
        if (not isinstance(checked_at, str)
                or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', checked_at)):
            raise ValueError('published_programs.checked_at needs a canonical UTC timestamp')
        try:
            datetime.datetime.strptime(checked_at, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError as error:
            raise ValueError('published_programs.checked_at needs a valid UTC timestamp') from error
        ids.add(name)
        paths.add(path)


def validate_reader_test(value):
    """Validate authored description without interpreting or deriving a method."""
    if not isinstance(value, dict) or set(value) != {'input', 'action', 'check'}:
        raise ValueError('reader_test needs input, action and check only')
    for name, sentence in value.items():
        if (not isinstance(sentence, str) or not sentence or sentence != sentence.strip()
                or len(sentence) > 320 or re.search(r'[<>]', sentence)
                or any(unicodedata.category(char) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'}
                       for char in sentence)):
            raise ValueError('reader_test.' + name + ' needs one plain trimmed paragraph of at most 320 characters')


def validate_published_program_collections(record):
    """Select bounded retained collections; member settings live only in output."""
    if 'published_program_collections' not in record:
        return
    collections = record['published_program_collections']
    if (not isinstance(collections, list) or not 1 <= len(collections) <= 32
            or any(not isinstance(item, dict) or set(item) != {'output', 'checked_at'}
                   for item in collections)):
        raise ValueError('published_program_collections needs 1–32 output and checked_at selections')
    singles = record.get('published_programs', [])
    if not isinstance(singles, list) or len(singles) + len(collections) > 32:
        raise ValueError('published_program_collections shares the 32 retained-file selection limit')
    paths = [item.get('output') for item in singles if isinstance(item, dict)]
    paths += [item['output'] for item in collections]
    if any(not isinstance(path, str) for path in paths) or len(set(paths)) != len(paths):
        raise ValueError('published_program_collections needs distinct retained-file selections')
    for item in collections:
        probe = {**record, 'published_programs': [{**item, 'id': 'retained-collection'}]}
        try:
            validate_published_programs(probe)
        except ValueError as error:
            raise ValueError('published_program_collections: ' + str(error)) from error


def article_bytes(raw):
    if raw.get('schema') != SCHEMA:
        return None
    analysis = raw.get('analysis')
    if not isinstance(analysis, str) or not analysis.strip():
        raise ValueError('V2 analysis must contain the technical account as Markdown')
    # Preserve exact authored bytes, including frozen historical line endings.
    return analysis.encode('utf-8')


def compile_content(raw):
    record = copy.deepcopy(raw)
    for key, limit in [('reader_title', 110), ('reader_intro', 280)]:
        if key in record:
            value = record[key]
            if (not isinstance(value, str) or not value or value != value.strip()
                    or len(value) > limit or re.search(r'[<>]', value)
                    or any(unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'} for ch in value)):
                raise ValueError(key + ' needs one plain trimmed paragraph of at most ' + str(limit) + ' characters')
    if 'reader_test' in record:
        validate_reader_test(record['reader_test'])
    validate_published_programs(record)
    validate_published_program_collections(record)
    if 'schema' not in record:
        return record
    if record['schema'] != SCHEMA:
        raise ValueError('Unsupported experiment content schema')
    duplicate = DERIVED.intersection(record)
    if duplicate:
        raise ValueError('V2 derives these fields; edit result or analysis instead: ' + ', '.join(sorted(duplicate)))
    classification = record.get('classification')
    if not isinstance(classification, dict) or set(classification) != {'kind', 'methods', 'map_parent'}:
        raise ValueError('V2 classification needs kind, methods and map_parent')
    result = record.get('result')
    if not isinstance(result, dict) or set(result) != {'finding', 'limits', 'next_steps'}:
        raise ValueError('V2 result needs finding, limits and next_steps only')
    for name, value in result.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError('V2 result.' + name + ' needs authored text')
        if len(value) > 700 or '\n' in value or '\r' in value:
            raise ValueError('V2 result.' + name + ' must be one paragraph of at most 700 characters; put technical detail in analysis')
    account = article_bytes(raw).decode('utf-8')
    if 'presentation' in record:
        presentation = record.pop('presentation')
        if not isinstance(presentation, dict) or set(presentation) != {'finding_sections'}:
            raise ValueError('V2 presentation supports finding_sections only')
        sections = presentation['finding_sections']
        if (not isinstance(sections, list) or len(sections) > 3
                or any(not isinstance(title, str) or not title or title != title.strip()
                       or len(title) > 120 or re.search(r'[\r\n<>]', title) for title in sections)
                or len(set(sections)) != len(sections)):
            raise ValueError('V2 finding_sections needs up to three distinct short heading titles')
        # The registry validator checks that each names one unambiguous authored H2.
        record['reader_sections'] = sections
    record.pop('schema')
    record.pop('result')
    record.pop('analysis')
    record.update(finding=result['finding'], summary=result['finding'],
                  reader_finding=result['finding'], limitations=result['limits'],
                  reader_limit=result['limits'], next_steps=result['next_steps'], article=account)
    return record


def draft_record_ids(root):
    """Only an explicit canonical v2 draft authorizes automatic withdrawal."""
    identifiers = []
    for path in sorted((root / 'experiments/records').glob('*/record.json')):
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Experiment source escapes repository')
        raw = json.loads(path.read_text(encoding='utf-8'))
        if raw.get('schema') == SCHEMA and raw.get('status') == 'draft':
            identifier = raw.get('id')
            if (not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier)
                    or path.parent.name != identifier):
                raise ValueError('Invalid or mismatched v2 draft ID')
            identifiers.append(identifier)
    return identifiers
