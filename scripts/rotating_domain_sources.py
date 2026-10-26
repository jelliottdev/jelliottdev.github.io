"""Detached complete rotating domains; never decode manuscript pages."""
import copy
import hashlib
import json
from pathlib import Path

import browser_followups as fixed
import build_local_run_inputs as inputs
import build_repeating_key_banks as banks
import pinned_domain_partitions as P

ROOT = Path(__file__).resolve().parents[1]
OPENINGS = 'experiments/records/lp2-known-vigenere-keys/plan.json'
VARIANTS = ('rotate-left', 'rotate-right')


def domain(root=ROOT, variant='rotate-left'):
    root = Path(root)
    fixed.require(variant in VARIANTS, 'unknown rotating domain')
    registry = P.MaintainedRegistry()
    bank = next(b for b in registry.list() if b['id'] == 'public-wordlist-' + variant + '-v1')
    for pin in bank['sourcePins']:
        fixed.require(hashlib.sha256((root / pin['path']).read_bytes()).hexdigest() == pin['sha256'],
                      'rotating source changed: ' + pin['path'])
    raw = (root / OPENINGS).read_bytes()
    # This opening-plan identity is already independently retained by the key source.
    import public_wordlist_followups as source
    fixed.require(hashlib.sha256(raw).hexdigest() == source.OPENING_PLAN_SHA256, 'opening source changed')
    bundle = json.loads(inputs.render(root))
    pins = copy.deepcopy(bank['sourcePins'])
    opening_pin = dict(path=OPENINGS, sha256=hashlib.sha256(raw).hexdigest())
    if opening_pin not in pins:
        pins.append(opening_pin)
    parent = dict(schema=P.SCHEMA,
                  aim=dict(outcomeId='decipher', detail='Check nine supplied openings using this complete historical schedule'),
                  bank=dict(bankId=bank['id'], bankSha256=bank['sha256'], start=0, count=bank['total']),
                  keyOperation=0, steps=[dict(op='keyed-shift', mode='repeat', direction='subtract', reset='page')],
                  inputVersion='raw', alphabetSha256=P.ALPHABET,
                  pages=[dict(id=p['id'], textSha256=fixed.text_hash(p['raw'])) for p in bundle['pages']
                         if p['id'].startswith('lp2-') and int(p['id'][4:]) <= 55 and p['id'] != 'lp2-50'],
                  criterion=dict(kind='exact-prefix-set', openings=[dict(id=o['id'], values=o['indices'])
                                                                 for o in json.loads(raw)['openings']]),
                  sourcePins=pins)
    P.prepare(parent, registry)
    return parent


def domains(root=ROOT):
    return {variant: domain(root, variant) for variant in VARIANTS}
