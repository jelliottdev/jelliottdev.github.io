"""Compile one authored experiment into the stable public record contract.

V2 record.json is the only authored content file. article.md and public aliases
are derived views; this module never writes files or executes experiments.
"""
import copy

SCHEMA = 'liberpedia-experiment-v2'
DERIVED = {'summary', 'finding', 'limitations', 'next_steps', 'reader_finding',
           'reader_limit', 'reader_question', 'article', 'article_path', 'reader_sections',
           'record_type', 'method_topics', 'script_sha256', 'article_links'}


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
    record.pop('schema')
    record.pop('result')
    record.pop('analysis')
    record.update(finding=result['finding'], summary=result['finding'],
                  reader_finding=result['finding'], limitations=result['limits'],
                  reader_limit=result['limits'], next_steps=result['next_steps'], article=account)
    return record
