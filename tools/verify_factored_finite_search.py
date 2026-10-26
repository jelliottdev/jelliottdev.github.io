"""Audit a factored finite snapshot and every advertised original-receipt chunk.

python verify_factored_finite_search.py manifest.json [--chunks-dir DIRECTORY]
No network, uploads or execution of missing cases. Original dates and locations
are not authenticated. Recorded lookup status is not an archive-absence proof.
"""
import argparse
import copy
from datetime import datetime
import hashlib
import itertools
import json
from pathlib import Path
import re
import verify_finite_search as old

runner = old.runner
require, fields = old.require, old.fields
MAX_MANIFEST = 8 * 1024 * 1024
MAX_CHUNK = 8 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_SOURCES = 76800
MAX_DOMAIN = 4 * 1024 * 1024
PATH = re.compile(r'^chunks/[0-9]{6}\.json$')
DERIVATION = 'The requested opening is evaluated now from independently replayed original transformed text. Original source criteria, verdicts and dates remain unchanged; no requested-experiment result receipt or historical test is created.'
OUTPUT_DERIVATION = 'The requested language comparison is evaluated now from independently replayed original transformed text. Original source criteria, verdicts and dates remain unchanged; no requested-experiment result receipt or historical test is created.'
INSPECTION_LIMIT = 'These receipts preserve the complete output of the declared transformations on the pinned texts. Completion means the declared outputs are ready to inspect; it does not decide language, readability or decryption. Outputs containing no runes still count as computed. Missing cases are absent from these receipts; they are not established as new work.'
INSPECTION_DERIVATION = 'The requested output inspection uses independently replayed original transformed text. Original source criteria, verdicts and dates remain unchanged; no requested-experiment result receipt or historical test is created.'
OUTPUT_LIMIT = 'These comparisons describe the declared outputs against the eight pinned reference texts and their 32 same-rune rearrangements. They do not identify a language or establish a decryption. Outputs with fewer than 40 runes are too short to compare. Missing cases are absent from these receipts; they are not established as new work.'


def bounded_json(raw, limit):
    require(len(raw) <= limit, 'JSON exceeds its byte budget')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=runner.unique_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Invalid number')))
    return old.bounded(value)


def read_bytes(path, limit):
    require(path.is_file() and not path.is_symlink(), 'A required ordinary file is missing')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'File exceeds its byte budget')
    return raw


def domain_check(original, q, output=False, inspection=False):
    fields(original, ('proposalId', 'card'), 'Original')
    card = original['card']
    require(original['proposalId'] == 'p_' + old.digest(card), 'Original proposal identity mismatch')
    operations, axes, count = old.declaration(card, max_cases=MAX_SOURCES, check_expanded_budget=False)
    fields(q, ('schema', 'questionPolicy', 'engine', 'inputVersion', 'alphabet', 'pages', 'criterion', 'programs', 'totalCases', 'id') if output
           else ('schema', 'engine', 'inputVersion', 'alphabet', 'pages', 'criterion', 'programs', 'totalCases', 'id'), 'Factored question')
    require(q['schema'] == ('liberpedia-factored-finite-output-question-v1' if output else 'liberpedia-factored-finite-question-v2') and q['engine'] == runner.ENGINE
            and q['inputVersion'] in ('raw', 'reviewed'), 'Unsupported factored domain')
    require(len(old.stable(q).encode('utf-8')) <= MAX_DOMAIN, 'Shared domain exceeds 4 MiB')
    require(q['id'] == old.digest({k: v for k, v in q.items() if k != 'id'}), 'Factored domain digest mismatch')
    require(card['rules']['inputVersion'] == {'status': 'specified', 'value': q['inputVersion']}
            and card['rules']['evaluation'] == {'status': 'specified', 'value': 'measurement' if inspection else q['criterion']}, 'Original edition/criterion changed')
    if inspection:
        require(q['questionPolicy'] == 'transformed-output-inspection-v1' and q['criterion'] == {'kind': 'measurement'}, 'The explicit output inspection changed')
    elif output:
        require(q['questionPolicy'] == 'language-reference-comparison-v1' and q['criterion'] ==
                {'kind': 'language-score', 'modelId': runner.LANGUAGE_MODEL_ID, 'modelSha256': runner.LANGUAGE_MODEL_SHA256}, 'The explicit pinned comparison changed')
    else:
        require(q['criterion'].get('kind') in ('exact-prefix', 'exact-prefix-set'), 'Only exact opening factored questions are supported')
    require([p['id'] for p in q['pages']] == sorted(card['scope']['value']['pages']), 'Shared scope changed')
    probe = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE, 'title': 'Offline factored geometry check',
             'alphabet': q['alphabet'], 'pages': q['pages'], 'steps': [], 'criterion': q['criterion']}
    old.task_check({**probe, 'taskId': old.digest(probe)})
    programs = {}
    for values in itertools.product(*(axis['values'] for axis in axes)):
        member = copy.deepcopy(operations)
        for axis, value in zip(axes, values):
            member[axis['operation']][axis['name']] = value
        steps = old.compile_steps(member, card['rules'])
        candidate = {**probe, 'steps': steps}
        # Maintained static checks cover every page/reset segment, not just the
        # first page. This never computes the output of a missing case.
        runner.validate({**candidate, 'taskId': old.digest(candidate)})
        identifier = old.protocol(q, steps)
        require(identifier not in programs, 'Duplicate compiled protocol')
        programs[identifier] = steps
    expected = [{'id': identifier, 'steps': programs[identifier]} for identifier in sorted(programs)]
    require(q['programs'] == expected, 'Factored programs do not exhaust the original declaration')
    require(type(q['totalCases']) is int and q['totalCases'] == count * len(q['pages'])
            and 1 <= q['totalCases'] <= MAX_SOURCES, 'Factored case count changed')
    return {p['id']: i for i, p in enumerate(q['programs'])}


def verify(manifest, directory):
    old.bounded(manifest)
    require(len(old.stable(manifest).encode('utf-8')) <= MAX_MANIFEST, 'Manifest exceeds 8 MiB')
    output = manifest.get('schema') == 'liberpedia-factored-finite-output-snapshot-v1'
    fields(manifest, ('schema', 'questionPolicy', 'original', 'question', 'evidence', 'proof', 'finding', 'snapshotId') if output
           else ('schema', 'original', 'question', 'evidence', 'proof', 'finding', 'snapshotId'), 'Manifest')
    inspection = output and manifest.get('questionPolicy') == 'transformed-output-inspection-v1'
    if output:
        require(manifest['questionPolicy'] in ('language-reference-comparison-v1', 'transformed-output-inspection-v1'), 'The output question policy changed')
    derived = manifest['schema'] == 'liberpedia-factored-finite-search-snapshot-v3'
    require(output or derived or manifest['schema'] == 'liberpedia-factored-finite-search-snapshot-v2', 'Unsupported snapshot schema')
    require(manifest['snapshotId'] == old.digest({k: v for k, v in manifest.items() if k != 'snapshotId'}), 'Snapshot digest mismatch')
    q, e = manifest['question'], manifest['evidence']
    programs = domain_check(manifest['original'], q, output, inspection)
    require(not derived or q['criterion']['kind'] != 'exact-prefix-set', 'Opening sets require direct original results')
    fields(e, ('chunks', 'lookup', 'provenanceMeaning', 'mode', 'derivationMeaning') if derived or output
           else ('chunks', 'lookup', 'provenanceMeaning'), 'Evidence')
    if output:
        require(e['mode'] == ('verified-output-inspection-v1' if inspection else 'verified-output-language-v1') and e['derivationMeaning'] == (INSPECTION_DERIVATION if inspection else OUTPUT_DERIVATION), 'Derived comparison meaning changed')
    if derived:
        require(e['mode'] == 'verified-output-prefix-v1' and e['derivationMeaning'] == DERIVATION, 'Derived evidence meaning changed')
    fields(e['lookup'], ('recordedComplete', 'meaning'), 'Recorded lookup')
    require(type(e['lookup']['recordedComplete']) is bool and e['lookup']['meaning'] == old.LOOKUP, 'Lookup is not an absence proof')
    require(e['provenanceMeaning'] == old.PROVENANCE, 'Original provenance meaning changed')
    chunks = e['chunks']
    require(isinstance(chunks, list) and len(chunks) <= MAX_SOURCES, 'Too many receipt chunks')
    expected_paths, total_bytes, declared_sources = set(), 0, 0
    for index, chunk in enumerate(chunks, 1):
        fields(chunk, ('path', 'sha256', 'bytes', 'entries'), 'Chunk reference')
        require(chunk['path'] == f'chunks/{index:06d}.json' and PATH.fullmatch(chunk['path']), 'Chunk path/order changed')
        require(isinstance(chunk['sha256'], str) and old.HEX.fullmatch(chunk['sha256']), 'Invalid chunk digest')
        require(type(chunk['bytes']) is int and 1 <= chunk['bytes'] <= MAX_CHUNK and type(chunk['entries']) is int
                and 1 <= chunk['entries'] <= 12, 'Invalid chunk size/count')
        expected_paths.add(chunk['path']); total_bytes += chunk['bytes']; declared_sources += chunk['entries']
    require(total_bytes <= MAX_TOTAL and declared_sources <= MAX_SOURCES, 'Receipt total exceeds audit budget')
    root = Path(directory).resolve()
    chunk_dir = root / 'chunks'
    if chunk_dir.exists():
        require(chunk_dir.is_dir() and not chunk_dir.is_symlink(), 'Chunk directory must be ordinary')
        observed = set()
        for file in chunk_dir.iterdir():
            require(file.is_file() and not file.is_symlink(), 'Unexpected directory or symbolic link among chunks')
            observed.add('chunks/' + file.name)
        require(observed == expected_paths, 'Missing or extra advertised chunks')
    else:
        require(not expected_paths, 'Required receipt chunks are missing')
    page_index = {p['id']: (i, p['text']) for i, p in enumerate(q['pages'])}
    coverage, matching = bytearray((q['totalCases'] + 7) // 8), bytearray((q['totalCases'] + 7) // 8)
    claims, receipts, replayed, owners = {}, set(), set(), {}
    insufficient = bytearray(len(coverage))
    for chunk in chunks:
        raw = read_bytes(root / chunk['path'], MAX_CHUNK)
        require(len(raw) == chunk['bytes'] and hashlib.sha256(raw).hexdigest() == chunk['sha256'], 'Chunk bytes or digest changed')
        contents = bounded_json(raw, MAX_CHUNK)
        fields(contents, ('schema', 'sources'), 'Receipt chunk')
        require(contents['schema'] == 'liberpedia-original-receipt-chunk-v1' and isinstance(contents['sources'], list)
                and len(contents['sources']) == chunk['entries'], 'Chunk source schema/count changed')
        for source in contents['sources']:
            fields(source, ('task', 'inputVersion', 'run'), 'Original source')
            run, task = source['run'], source['task']
            fields(run, ('id', 'createdAt', 'result'), 'Original result receipt')
            require(source['inputVersion'] == q['inputVersion'], 'Original source edition changed')
            old.task_check(task)
            require(len(old.stable(task).encode('utf-8')) <= 2000000 and len(old.stable(run['result']).encode('utf-8')) <= 2000000,
                    'Original task/result exceeds its maintained byte budget')
            require(run['id'] == old.digest(run['result']), 'Original result digest changed')
            date = run['createdAt']
            require(isinstance(date, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', date), 'Invalid original source date')
            datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
            key = (task['taskId'], run['id'], source['inputVersion'], date)
            require(key not in receipts, 'Duplicate original receipt')
            receipts.add(key)
            require(task['engine'] == q['engine'] and task['alphabet'] == q['alphabet'], 'Source changed its exact transformation')
            direct = task['criterion'] == q['criterion']
            require(direct or (derived and task['criterion']['kind'] in ('measurement', 'exact-prefix')) or (output and task['criterion']['kind'] in ('measurement', 'exact-prefix', 'exact-prefix-set', 'word-affine-count', 'word-prime-sums', 'language-score')), 'Source changed its exact common protocol')
            protocol_id = old.protocol(q, task['steps'])
            require(protocol_id in programs, 'Original source is outside the declared programs')
            pair = (task['taskId'], run['id'])
            if pair not in replayed:
                result = runner.run(task)
                require(old.stable(result) == old.stable(run['result']), 'Original result failed independent replay')
                replayed.add(pair)
            relevant = False
            for page in task['pages']:
                target = page_index.get(page['id'])
                if target is None or target[1] != page['text']:
                    continue
                relevant = True
                position = programs[protocol_id] * len(q['pages']) + target[0]
                match = next(m['matched'] for m in run['result']['matches'] if m['page'] == page['id']) if direct and not output else False
                text = next(p['text'] for p in run['result']['transformed'] if p['page'] == page['id'])
                if not direct and not output:
                    indices = {entry['rune']: i for i, entry in enumerate(q['alphabet'])}
                    values = [indices[ch] for ch in text if ch in indices]
                    match = values[:len(q['criterion']['values'])] == q['criterion']['values']
                if output:
                    if inspection:
                        rune_set = {entry['rune'] for entry in q['alphabet']}
                        assessment = {'status': 'rune-output' if any(ch in rune_set for ch in text) else 'no-runes'}
                    elif direct:
                        assessment = next(p for p in run['result']['languageScore']['pages'] if p['page'] == page['id'])
                    else:
                        indices = {entry['rune']: i for i, entry in enumerate(q['alphabet'])}
                        assessment = runner.language_evaluate([indices[ch] for ch in text if ch in indices])
                    require(assessment['status'] in (('rune-output', 'no-runes') if inspection else ('compared', 'insufficient')), 'An original comparison status changed')
                    signature = old.digest({'text': text, 'status': assessment['status']})
                    if assessment['status'] == ('no-runes' if inspection else 'insufficient'):
                        insufficient[position >> 3] |= 1 << (position & 7)
                else:
                    signature = old.digest({'text': text, 'matched': match})
                require(position not in claims or claims[position] == signature, 'Conflicting exact case output')
                claims[position] = signature
                if derived or output:
                    owner = (0 if direct else 1, old.stable([task['taskId'], run['id'], date, source['inputVersion']]))
                    if position not in owners or owner < owners[position]:
                        owners[position] = owner
                coverage[position >> 3] |= 1 << (position & 7)
                if match:
                    matching[position >> 3] |= 1 << (position & 7)
            require(relevant, 'Original source has no exact page intersection')
    covered_count = len(claims)
    matched_count = sum(bin(byte).count('1') for byte in matching)
    proof = {'coveredCases': covered_count, 'matchingCases': matched_count, 'remainingCases': q['totalCases'] - covered_count,
             'complete': covered_count == q['totalCases'], 'coverageSha256': hashlib.sha256(coverage).hexdigest(),
             'matchingSha256': hashlib.sha256(matching).hexdigest()}
    if output:
        insufficient_count = sum(bin(byte).count('1') for byte in insufficient)
        proof = {'coveredCases': covered_count, ('runeOutputCases' if inspection else 'usableCases'): covered_count - insufficient_count,
                 ('noRuneCases' if inspection else 'insufficientCases'): insufficient_count, 'remainingCases': q['totalCases'] - covered_count,
                 'complete': covered_count == q['totalCases'], 'coverageSha256': hashlib.sha256(coverage).hexdigest(),
                 ('noRuneSha256' if inspection else 'insufficientSha256'): hashlib.sha256(insufficient).hexdigest()}
    if derived or output:
        derived_coverage = bytearray(len(coverage))
        for position, owner in owners.items():
            if owner[0] == 1:
                derived_coverage[position >> 3] |= 1 << (position & 7)
        derived_count = sum(1 for owner in owners.values() if owner[0] == 1)
        proof.update(directCases=covered_count - derived_count, derivedCases=derived_count,
                     derivedCoverageSha256=hashlib.sha256(derived_coverage).hexdigest())
        require(type(manifest['proof'].get('directCases')) is int and type(manifest['proof'].get('derivedCases')) is int, 'Derived coverage count types changed')
    if output:
        proof['evidenceMode'] = 'verified-output-inspection-v1' if inspection else 'verified-output-language-v1'
    fields(manifest['proof'], tuple(proof), 'Coverage proof')
    require(all(type(manifest['proof'][key]) is int for key in (('coveredCases', 'runeOutputCases', 'noRuneCases', 'remainingCases') if inspection else ('coveredCases', 'usableCases', 'insufficientCases', 'remainingCases') if output else ('coveredCases', 'matchingCases', 'remainingCases')))
            and type(manifest['proof']['complete']) is bool
            and all(isinstance(manifest['proof'][key], str) and old.HEX.fullmatch(manifest['proof'][key]) for key in (('coverageSha256', 'noRuneSha256') if inspection else ('coverageSha256', 'insufficientSha256') if output else ('coverageSha256', 'matchingSha256'))), 'Coverage proof types changed')
    require(manifest['proof'] == proof, 'Coverage counts or bitmap digests changed')
    answer = (('outputs-ready' if inspection else 'comparisons-complete') if proof['complete'] else 'incomplete') if output else 'prefix-found' if matched_count and (proof['complete'] or q['criterion']['kind'] != 'exact-prefix-set') else 'prefix-not-found' if proof['complete'] else 'incomplete'
    limit = INSPECTION_LIMIT if inspection else OUTPUT_LIMIT if output else old.LIMIT
    require(manifest['finding'] == {'kind': answer, 'limit': limit}, 'Finding or scientific limit changed')
    return {'snapshotId': manifest['snapshotId'], 'domainId': q['id'], 'finding': answer, **proof,
            'replayedSources': len(replayed), 'originalReceipts': len(receipts),
            'recordedLookupComplete': e['lookup']['recordedComplete'], 'lookupMeaning': old.LOOKUP, 'limit': limit}


def audit_file(manifest_path, directory=None):
    filename = Path(manifest_path)
    return verify(bounded_json(read_bytes(filename, MAX_MANIFEST), MAX_MANIFEST), filename.parent if directory is None else directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest'); parser.add_argument('--chunks-dir')
    args = parser.parse_args()
    try:
        print(json.dumps(audit_file(args.manifest, args.chunks_dir), ensure_ascii=False, indent=2))
    except (ValueError, TypeError, KeyError, UnicodeError, OSError, OverflowError) as error:
        parser.exit(1, 'Factored snapshot verification failed: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
