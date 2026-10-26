"""Audit saved source arrays and build four bounded sequence banks.

No original program is imported or executed. Independent number theory checks
raw archived streams; inverse arithmetic checks every stored output. Generated
banks do not assert any new language/reset result or reproduce a browser run.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path

import finite_sequence_banks as banks

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PINS = {
 'lp2-prime-minus-one-openings': ('prime-minus-one-v1', {
  'plan.json': '61013e70fe327294168831fc53889c4cbad54e5bd22e801b6b8b06296973917a',
  'results.json': 'c2e1572cb2a10ac53cdb8bc3c0f9ffd46a494278c5cd97fcf8f23a6d86aa836b',
  'run.py': '72175c2a653105f325e22d28be3458646ae7ed3dd5f868cfe80870ef27ef4f79',
  'check.py': '58a9311e6a622374b5d087dcf185525d19703a8d70c15140913f031d4fc8ce8f'}),
 'lp2-prime-openings': ('prime-v1', {
  'plan.json': '7348fa88c1300e504d099c1027fa5ef8c03ed28f686fe1df29bee77cd6512274',
  'results.json': '3f7ebb3f7e5f2ee2cf2ddf518a5546b76d11056d96b3a6dcbb3c8930e61240f3',
  'run.py': '4f45a282ea5137ee6da3323357ecaa3698ee765b716e8dfcac930d3afe205635',
  'check.py': 'b3c1a37cd3fe2a52cfcbbce26d748188536dbadeab7de38e49751ce99a96405a'}),
 'lp2-fibonacci-openings': ('fibonacci-v1', {
  'plan.json': '260b0040349ce426064d87c5d0b51481b25f29cbb7fd43560d55c2e7dec9812b',
  'results.json': 'f29635492567ea137d6d9b45a2079dd5f33b9a9ea98262dde9a1b97a66c7af26',
  'run.py': '09caa98d544adea0c3cd79f736d114295ec798e3be4f249fbbad8ea03ed075b5',
  'check.py': '0121421c0fbd1c2aa31f75c6e2e1e72e28c21057a7b26a066054b24b7082279a'}),
 'lp2-totient-openings': ('totient-v1', {
  'plan.json': 'cb09778b854deedfa473486798b968d9315b60f0e8a13fd697b84f34ca890324',
  'results.json': '15e2a0e36e139d8cdcd0652225566b9071f81e79ba0efc72606f697730b225ae',
  'run.py': 'c3ec24c0961e29b34f6c2592eea5c5b18a72f5ff77dd1df759af3fcd1408661f',
  'check.py': '7fe64c64833d775d10c43d6796a89c6381d2d8d5d73253e9b916e000b05baaac'})}
require = banks.require
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def raw_sequence(identifier):
    if identifier in ('prime-v1', 'prime-minus-one-v1'):
        result, n = [], 2
        while len(result) < 305:
            if all(n % divisor for divisor in range(2, math.isqrt(n) + 1)):
                result.append(n - (identifier == 'prime-minus-one-v1'))
            n += 1
        return result
    if identifier == 'fibonacci-v1':
        def pair(n):
            if not n:
                return 0, 1
            a, b = pair(n // 2)
            c, d = a * (2 * b - a), a * a + b * b
            return (d, c + d) if n % 2 else (c, d)
        return [pair(n)[0] for n in range(305)]
    require(identifier == 'totient-v1', 'unknown raw sequence')
    return [sum(math.gcd(n, k) == 1 for k in range(1, n + 1)) for n in range(1, 306)]


def audit_source(record_id, root=ROOT):
    root = Path(root)
    require(record_id in SOURCE_PINS, 'unknown source record')
    identifier, pins = SOURCE_PINS[record_id]
    folder = root / 'experiments/records' / record_id
    documents = {}
    for name, pin in pins.items():
        raw = (folder / name).read_bytes()
        require(sha(raw) == pin, 'frozen source changed: ' + record_id + '/' + name)
        if name.endswith('.json'):
            documents[name] = json.loads(raw)
    plan, report = documents['plan.json'], documents['results.json']
    require(report['plan_sha256'] == pins['plan.json'], 'report plan binding changed')
    for item in plan['inputs']:
        path = Path(item['path'])
        require(not path.is_absolute() and '..' not in path.parts, 'unsafe source input')
        require(sha((root / path).read_bytes()) == item['sha256'], 'source input changed: ' + item['path'])
    pages = ['lp2-%02d' % n for n in range(56)]
    require(plan['pages'] == pages and plan['offsets'] == list(range(29))
            and plan['signs'] == [-1, 1] and plan['prefix_length'] == 12, 'source grid changed')
    sequence = raw_sequence(identifier)
    require(type(report['shifts']) is list and all(type(n) is int for n in report['shifts'])
            and report['shifts'] == sequence, 'independent raw sequence differs')
    values = [n % 29 for n in sequence]
    descriptor = {'id': identifier, 'sha256': banks.bank_hash(identifier, values), 'values': values}
    require(descriptor['sha256'] == banks.PINS[identifier], 'known bank pin differs')
    alphabet = [row['rune'] for row in json.loads((root / 'data/index.json').read_bytes())['alphabet']]
    require(len(alphabet) == len(set(alphabet)) == 29, 'alphabet changed')
    lookup = {rune: n for n, rune in enumerate(alphabet)}
    streams, page_pins = {}, []
    official = {p['id']: p for p in json.loads((root / 'data/local-run-inputs.json').read_bytes())['pages']}
    for page in pages:
        raw = (root / 'text' / (page + '.txt')).read_bytes()
        text = raw.decode('utf8')
        require(not {c for c in text if '\u16a0' <= c <= '\u16ff'} - set(alphabet), 'unknown rune')
        require(text == official[page]['raw'] == json.loads((root / 'data/pages' / (page + '.json')).read_bytes())['raw'], 'official raw text differs')
        streams[page] = [lookup[c] for c in text if c in lookup]
        page_pins.append({'id': page, 'textSha256': sha(raw), 'runes': len(streams[page])})
    require(max(map(len, streams.values())) == 277 and report['page_lengths'] == {p: len(s) for p, s in streams.items()}
            and report['empty_pages'] == ['lp2-50'], 'page geometry changed')
    openings = plan['openings']
    require(len(openings) == 9 and len({o['id'] for o in openings}) == 9, 'nine named openings required')
    for opening in openings:
        raw = (root / opening['source']).read_bytes()
        require(sha(raw) == opening['sha256'], 'opening source pin changed')
        rows = list(csv.DictReader(io.StringIO(raw.decode('utf8'))))
        require([int(row['output_index']) for row in rows[:12]] == opening['indices']
                and len(opening['indices']) == 12 and all(type(n) is int and 0 <= n < 29 for n in opening['indices']), 'opening vector differs')
    expected = {(p, offset, sign) for p in pages if streams[p] for offset in range(29) for sign in (-1, 1)}
    seen, matches, rune_total, distinct, case_map = set(), 0, 0, {p: set() for p in pages}, {}
    for case in report['cases']:
        identity = case['page'], case['offset'], case['sign']
        require(identity in expected and identity not in seen and type(case['offset']) is int
                and type(case['sign']) is int, 'missing/duplicate/foreign source setting')
        seen.add(identity)
        page, offset, sign = identity
        output, ciphertext = case['output_indices'], streams[page]
        require(type(output) is list and len(output) == len(ciphertext), 'incomplete archived output')
        for n, (value, source) in enumerate(zip(output, ciphertext)):
            require(type(value) is int and 0 <= value < 29
                    and (value - sign * values[offset + n]) % 29 == source, 'archived output inverse mismatch')
        declared_matches = [opening['id'] for opening in openings if output[:12] == opening['indices']]
        require(case['matching_openings'] == declared_matches, 'archived opening decision differs')
        matches += bool(declared_matches)
        rune_total += len(output)
        distinct[page].add(tuple(output))
        case_map[identity] = tuple(output)
    require(seen == expected and report['case_count'] == len(expected) == 3190
            and report['comparison_count'] == len(expected) * 9 == 28710
            and report['matching_case_count'] == matches == 0, 'original counters differ')
    distinct_count = sum(map(len, distinct.values()))
    if 'distinct_page_outputs' in report:
        require(report['distinct_page_outputs'] == distinct_count, 'distinct output count differs')
    aliases = []
    if identifier == 'fibonacci-v1':
        states = [(values[i], values[i + 1]) for i in range(15)]
        require(states[0] == states[14] == (0, 1) and len(set(states[:14])) == 14
                and report['residue_period'] == 14 and report['residue_cycle'] == values[:14], 'Fibonacci period differs')
        aliases = [{'offset': n, 'equivalentOffsetWithinAudited277Runes': n % 14} for n in range(29)]
        for (page, offset, sign), output in case_map.items():
            require(output == case_map[page, offset % 14, sign], 'Fibonacci source alias differs')
    audit = {'recordId': record_id, 'bankId': identifier, 'sourcePins': pins, 'sourceInputs': plan['inputs'],
             'pagePins': page_pins, 'openings': openings, 'namedOffsets': list(range(29)), 'signs': [-1, 1],
             'archivedArrays': 3190, 'archivedOutputRunes': rune_total, 'openingComparisons': 28710,
             'openingMatches': matches, 'distinctPageOutputs': distinct_count, 'emptyPages': ['lp2-50'],
             'maximumPageRunes': 277, 'bankTerms': 305, 'fibonacciAliases': aliases,
             'sourceControl': plan['control'], 'method': 'Independent raw arithmetic plus inverse verification of every saved output; no source script or target decoder executed.'}
    return descriptor, audit


def javascript(descriptors):
    # Small synchronous integrity hash copied from the maintained SHA-256
    # implementation. No external runtime, network or asynchronous model load.
    language = (ROOT / 'language-score.js').read_text(encoding='utf8')
    start, end = language.index(' function sha256(text){'), language.index(' function freeze(value)')
    hasher = language[start:end]
    literal = banks.stable(descriptors)
    pins = banks.stable(banks.PINS)
    return '''/* Generated bounded sequence banks. Rebuild: python scripts/build_finite_sequence_banks.py --write */
(function(root){
 'use strict';
 const BANKS=''' + literal + ''',PINS=''' + pins + ''';
 const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
''' + hasher + '''
 const map=new Map();
 for(const bank of BANKS){if(Object.keys(bank).length!==3||map.has(bank.id)||!Object.hasOwn(PINS,bank.id)||bank.sha256!==PINS[bank.id]||!Array.isArray(bank.values)||bank.values.length!==305||!bank.values.every(n=>Number.isInteger(n)&&n>=0&&n<29)||sha256(stable({schema:'liberpedia-finite-sequence-bank-v1',id:bank.id,values:bank.values}))!==bank.sha256)throw Error('Finite sequence bank integrity failed.');Object.freeze(bank.values);Object.freeze(bank);map.set(bank.id,bank);}
 if(BANKS.length!==4||map.size!==4)throw Error('Finite sequence bank set is incomplete.');Object.freeze(BANKS);Object.freeze(PINS);
 function get(id,sha){if(typeof id!=='string'||typeof sha!=='string'||!map.has(id)||sha!==PINS[id])throw Error('Unknown finite sequence bank or hash.');const bank=map.get(id);return {id:bank.id,sha256:bank.sha256,values:bank.values.slice()};}
 function resolve(id,sha,offset){if(!Number.isInteger(offset)||offset<0||offset>28)throw Error('Audited offset must be an integer 0..28.');return get(id,sha).values.slice(offset);}
 const api=Object.freeze({get,resolve});if(typeof module==='object'&&module.exports)module.exports=api;else root.FiniteSequenceBanks=api;
})(typeof globalThis==='object'?globalThis:this);
'''


def build(write=False, root=ROOT):
    root = Path(root)
    descriptors, audits = [], []
    for record in SOURCE_PINS:
        descriptor, audit = audit_source(record, root)
        descriptors.append(descriptor)
        audits.append(audit)
    value = {'schema': 'finite-sequence-banks-v1', 'banks': descriptors,
             'sourceAudit': {'kind': 'audited-historical-output-projection', 'date': '2026-10-26',
                'dateMeaning': 'Independent storage-bank audit date, not a historical browser execution receipt.',
                'archivedArrays': sum(a['archivedArrays'] for a in audits),
                'openingComparisons': sum(a['openingComparisons'] for a in audits),
                'scope': 'Stored305terms only; offsets0..28; no continuation, repeat or authority beyond the finite bank. Future language/reset checks are new explicit evaluations, not reproduction of the nine-opening criterion.',
                'sources': audits}}
    outputs = {root / 'data/finite-sequence-banks.json': banks.stable(value) + '\n',
               root / 'finite-sequence-banks.js': javascript(descriptors)}
    for path, text in outputs.items():
        if write:
            path.write_text(text, encoding='utf8', newline='\n')
        else:
            require(path.exists() and path.read_bytes() == text.encode('utf8'), 'generated bank file is stale: ' + path.name)
    return value


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    value = build(write=args.write)
    print(json.dumps({'banks': len(value['banks']), 'auditedArrays': value['sourceAudit']['archivedArrays'],
                      'openingComparisons': value['sourceAudit']['openingComparisons'], 'targetExecutions': 0}))
