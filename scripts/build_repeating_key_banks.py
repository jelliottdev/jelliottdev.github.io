"""Pin source keys and bounded distinct rotation domains; never compute target output.

Ordering is numeric lexicographic over complete index vectors, with a shorter
prefix first. Exact duplicates are removed; cyclic-equivalent vectors of
different starting places remain separate unless their complete vectors match.
Arithmetic direction is not a key: 309 rotations give 618 two-sign settings.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'liberpedia-repeating-key-banks-v1'
PINS = {
 'experiments/records/public-wordlist-vigenere/plan.json': 'f988c9d2ec1b0040a59025253b23752721627edc081c6cc4659e6e8cb417107c',
 'experiments/records/public-wordlist-vigenere/results.json': '282804f80e5e31ee5e6982264935e4ceef031432ec626c4090bb6aa937820d0c',
 'experiments/records/wholepage-public-wordlist/plan.json': '8817b67b81e1e3cd0f5325aae099207cd0f907a469fec445219fff463eca4f05',
 'experiments/records/wholepage-public-wordlist/results.json': '998a15cf52882f413464540df321937372c11c6970da14e505af6b319ca4c454',
}
SCHEDULE_PINS = {
 'experiments/suites/classical-key-schedules/manifest.json': 'e35dc47b5b7ed57e63dc9772a237053646dc3189966f7eba7aff51a3dcf840ae',
 'experiments/suites/classical-key-schedules/engine.py': '6a455af606fc1c807d6628996c32d367b5d8bad87ee33e57d48c78b562428be8',
 'experiments/records/rotating-folded-key-openings/results.json': 'e87fead83ce73ba0b85819d93c13388e0dddcf6505de703a3ed68041b817da0a',
}
VARIANTS = ('rotate-left', 'rotate-right', 'fold-repeat-endpoints', 'fold-skip-endpoints')


def shortest_cycle(values):
    return next(values[:n] for n in range(1, len(values) + 1) if len(values) % n == 0 and values == values[:n] * (len(values) // n))


def schedule(key, variant):
    key = tuple(key)
    if variant == 'rotate-left':
        whole = sum((key[q:] + key[:q] for q in range(len(key))), ())
    elif variant == 'rotate-right':
        whole = sum((key[-q:] + key[:-q] for q in range(len(key))), ())
    elif variant == 'fold-repeat-endpoints':
        whole = key + key[::-1]
    elif variant == 'fold-skip-endpoints':
        whole = key + key[-2:0:-1]
    else:
        raise ValueError('Unknown historical schedule variant')
    return shortest_cycle(whole)


def schedule_census(seeds):
    named, complete = {}, set()
    for variant in VARIANTS:
        count = 0
        for key in seeds:
            cycle = schedule(key, variant)
            count += len(cycle)
            complete.update(cycle[i:] + cycle[:i] for i in range(len(cycle)))
        named[variant] = count
    return dict(recordId='rotating-folded-key-openings', historicalSettings=sum(named.values()), distinctFullVectors=len(complete), variantSettings=named, maximumPeriod=max(map(len, complete)), repeatingKeyLimit=256, overLimitVectors=sum(len(k) > 256 for k in complete), overLimitPeriods=sorted({len(k) for k in complete if len(k) > 256}))


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(stable(value).encode()).hexdigest()


def vectors(bank):
    seeds = bank['seeds']
    if bank['rule'] == 'source-keys-v1':
        return [list(k) for k in sorted(set(tuple(k) for k in seeds))]
    if bank['rule'] == 'all-rotations-v1':
        return [list(k) for k in sorted({tuple(k[i:] + k[:i]) for k in seeds for i in range(len(k))})]
    if bank['rule'] in tuple(variant + '-v1' for variant in VARIANTS):
        cycles = [schedule(k, bank['variant']) for k in seeds]
        return [list(k) for k in sorted({cycle[i:] + cycle[:i] for cycle in cycles for i in range(len(cycle))})]
    raise ValueError('Unknown repeating key bank rule')


def prepare(root=ROOT):
    root = Path(root)
    source = {}
    for path, pin in {**PINS, **SCHEDULE_PINS}.items():
        raw = (root / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError('Repeating key bank source pin changed: ' + path)
        source[path] = json.loads(raw) if path.endswith('.json') else raw
    alphabet = json.loads((root / 'data/local-run-inputs.json').read_bytes())['alphabet']
    if digest(alphabet) != '06d9b994e762c485c2ce5d6a5f0878258d8277e1e8afa3178d41a29a97c5c73f':
        raise ValueError('The canonical GP29 table changed')
    lookup = {r['rune']: i for i, r in enumerate(alphabet)}
    plan = source['experiments/records/public-wordlist-vigenere/plan.json']
    original = source['experiments/records/public-wordlist-vigenere/results.json']
    whole_plan = source['experiments/records/wholepage-public-wordlist/plan.json']
    whole_result = source['experiments/records/wholepage-public-wordlist/results.json']
    if len(plan['keys']) != 43 or [k['id'] for k in plan['keys']] != ['key-%02d' % n for n in range(1, 44)]:
        raise ValueError('The complete named source key order changed')
    seeds = sorted({tuple(lookup[r] for r in k['runes']) for k in plan['keys']})
    if len(seeds) != 43 or sum(map(len, seeds)) != 309:
        raise ValueError('The source key domain changed')
    if original['key_count'] != 43 or original['plan_sha256'] != PINS['experiments/records/public-wordlist-vigenere/plan.json']:
        raise ValueError('The original source result does not bind the key plan')
    if whole_plan['settings_count'] != 618 or whole_result['setting_count'] != 618 or whole_result['plan_sha256'] != PINS['experiments/records/wholepage-public-wordlist/plan.json']:
        raise ValueError('The rotation/sign source domain changed')
    banks = []
    for bank_id, label, rule, total, settings in [
        ('public-wordlist-keys-v1', 'Archived wordlist keys', 'source-keys-v1', 43, 43),
        ('public-wordlist-rotations-v1', 'Archived wordlist keys at every starting place', 'all-rotations-v1', 309, 618),
    ]:
        bank = dict(id=bank_id, label=label, rule=rule, total=total, sourcePins=[dict(path=p, sha256=h) for p, h in sorted(PINS.items())], seeds=[list(k) for k in seeds], historicalSettings=settings)
        if len(vectors(bank)) != total:
            raise ValueError('The distinct vector count changed')
        bank['sha256'] = digest(bank)
        banks.append(bank)
    manifest = source['experiments/suites/classical-key-schedules/manifest.json']
    result = source['experiments/records/rotating-folded-key-openings/results.json']
    audit = schedule_census(seeds)
    expected = dict(zip(VARIANTS, (2561, 2561, 618, 532)))
    if (manifest['source_keys_sha256'] != PINS['experiments/records/public-wordlist-vigenere/plan.json']
            or manifest['records']['rotating-folded-key-openings']['variants'] != list(VARIANTS)
            or result['manifest_sha256'] != SCHEDULE_PINS['experiments/suites/classical-key-schedules/manifest.json']
            or result['key_plan_sha256'] != PINS['experiments/records/public-wordlist-vigenere/plan.json']
            or result['configuration_count'] != 6272 or audit['historicalSettings'] != 6272
            or audit['distinctFullVectors'] != 6272 or audit['variantSettings'] != expected
            or audit['overLimitVectors'] != 648 or audit['overLimitPeriods'] != [324]
            or any(result['variants'][variant]['configurations'] != count for variant, count in expected.items())):
        raise ValueError('The complete historical schedule census changed')
    for variant, label in [('fold-repeat-endpoints', 'Historical folded keys — repeat endpoints'), ('fold-skip-endpoints', 'Historical folded keys — skip endpoints'), ('rotate-left', 'Historical rotating keys — left'), ('rotate-right', 'Historical rotating keys — right')]:
        bank = dict(id='public-wordlist-' + variant + '-v1', label=label, rule=variant + '-v1', total=expected[variant], sourcePins=[dict(path=p, sha256=h) for p, h in sorted({**PINS, **SCHEDULE_PINS}.items())], seeds=[list(k) for k in seeds], historicalSettings=expected[variant], variant=variant, sourceAudit=audit)
        maximum = 324 if variant.startswith('rotate-') else 256
        if len(vectors(bank)) != bank['total'] or any(len(k) > maximum for k in vectors(bank)):
            raise ValueError('The complete named schedule vector census changed')
        bank['sha256'] = digest(bank)
        banks.append(bank)
    return dict(schema=SCHEMA, banks=banks)


LOOKUP_SCHEMA = 'liberpedia-repeating-key-ordinal-index-v1'
LOOKUP_ENCODING = 'seed6-phase9-u16be-base64url-v1'
LOOKUP_ORDER = 'numeric-lexicographic-distinct-full-vectors-v1'


def lookup_index(data):
    """Compile ordinal representation only; semantic bank definitions stay exact.

    A source ordinal names one complete vector. The extra lookup pin does not
    replace the source bank SHA or alter ordering, periods, bounds or findings.
    """
    entries = []
    for bank in data['banks']:
        representatives, periods = {}, []
        for seed_index, seed in enumerate(bank['seeds']):
            cycle = list(schedule(seed, bank['variant'])) if 'variant' in bank else list(seed)
            period = len(cycle)
            if seed_index >= 43 or not 1 <= period <= (324 if bank['rule'].startswith('rotate-') else 256):
                raise ValueError('A complete source cycle exceeds the existing representation bound')
            periods.append(period)
            phases = [0] if bank['rule'] == 'source-keys-v1' else range(period)
            for phase in phases:
                vector = tuple(cycle[phase:] + cycle[:phase])
                pair = (seed_index, phase)
                representatives[vector] = min(representatives.get(vector, pair), pair)
        ordered = sorted(representatives)
        if len(ordered) != bank['total'] or [list(v) for v in ordered] != vectors(bank):
            raise ValueError('Compiled ordinals differ from independent complete-vector ordering')
        packed = b''.join(((representatives[v][0] << 9) | representatives[v][1]).to_bytes(2, 'big') for v in ordered)
        basis = dict(bankId=bank['id'], bankSha256=bank['sha256'], total=bank['total'],
                     periods=periods, ordinals=base64.urlsafe_b64encode(packed).decode().rstrip('='))
        entries.append(dict(**basis, sha256=digest(dict(encoding=LOOKUP_ENCODING, order=LOOKUP_ORDER, **basis))))
    return dict(schema=LOOKUP_SCHEMA, encoding=LOOKUP_ENCODING, order=LOOKUP_ORDER, entries=entries)


def resolve(descriptor):
    if type(descriptor) is not dict or set(descriptor) != {'bankId', 'bankSha256', 'start', 'count'}:
        raise ValueError('Use an exact repeating key bank slice')
    data = json.loads((ROOT / 'data/repeating-key-banks.json').read_bytes())
    if data != prepare():
        raise ValueError('The maintained repeating key banks changed')
    bank = next((b for b in data['banks'] if b['id'] == descriptor['bankId'] and b['sha256'] == descriptor['bankSha256']), None)
    start, count = descriptor['start'], descriptor['count']
    if bank is None or type(start) is not int or type(count) is not int or start < 0 or not 1 <= count <= 1024 or start + count > bank['total']:
        raise ValueError('Repeating key bank slice is outside its exact bounds')
    return vectors(bank)[start:start + count]


RUNTIME = r'''
 const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Reflect.ownKeys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k))&&Object.values(Object.getOwnPropertyDescriptors(v)).every(d=>Object.hasOwn(d,'value')&&d.enumerable);
 const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;};
 const map=new Map(),lookupMap=new Map(),cycles=new Map();
 for(const bank of DATA.banks){const {sha256:pin,...basis}=bank,folded=Object.hasOwn(bank,'variant');if(!exact(bank,['id','label','rule','total','sourcePins','seeds','historicalSettings','sha256',...(folded?['variant','sourceAudit']:[])])||map.has(bank.id)||PINS[bank.id]!==pin||sha256(stable(basis))!==pin||!['source-keys-v1','all-rotations-v1','fold-repeat-endpoints-v1','fold-skip-endpoints-v1','rotate-left-v1','rotate-right-v1'].includes(bank.rule)||!Number.isSafeInteger(bank.total)||bank.total<1||!Array.isArray(bank.seeds)||bank.seeds.length!==43||bank.seeds.some(k=>!Array.isArray(k)||!k.length||k.length>256||k.some(n=>!Number.isInteger(n)||n<0||n>28)))throw Error('Repeating key bank integrity failed.');map.set(bank.id,bank);}
 if(DATA.schema!=='liberpedia-repeating-key-banks-v1'||map.size!==Object.keys(PINS).length||map.size<1)throw Error('The repeating key bank set changed.');freeze(DATA);freeze(PINS);
 const alphabet64='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
 function byteAt(text,index){const offset=Math.floor(index/3)*4,part=index%3,a=alphabet64.indexOf(text[offset]),b=alphabet64.indexOf(text[offset+1]);if(part===0)return (a<<2)|(b>>>4);const c=alphabet64.indexOf(text[offset+2]);return part===1?((b&15)<<4)|(c>>>2):((c&3)<<6)|alphabet64.indexOf(text[offset+3]);}
 function ordinal(entry,index){return (byteAt(entry.ordinals,index*2)<<8)|byteAt(entry.ordinals,index*2+1);}
 if(!exact(LOOKUP,['schema','encoding','order','entries'])||LOOKUP.schema!=='liberpedia-repeating-key-ordinal-index-v1'||LOOKUP.encoding!=='seed6-phase9-u16be-base64url-v1'||LOOKUP.order!=='numeric-lexicographic-distinct-full-vectors-v1'||!Array.isArray(LOOKUP.entries)||LOOKUP.entries.length!==map.size)throw Error('Repeating key lookup integrity failed.');
 for(const entry of LOOKUP.entries){const {sha256:pin,...basis}=entry,bank=map.get(entry.bankId),bytes=entry.total*2;
  if(!exact(entry,['bankId','bankSha256','total','periods','ordinals','sha256'])||!bank||lookupMap.has(entry.bankId)||entry.bankSha256!==bank.sha256||entry.total!==bank.total||LOOKUP_PINS[entry.bankId]!==pin||sha256(stable({encoding:LOOKUP.encoding,order:LOOKUP.order,...basis}))!==pin||!Array.isArray(entry.periods)||entry.periods.length!==43||entry.periods.some(n=>!Number.isSafeInteger(n)||n<1||n>(bank.rule.startsWith('rotate-')?324:256))||typeof entry.ordinals!=='string'||entry.ordinals.length!==Math.ceil(bytes*8/6)||/[^A-Za-z0-9_-]/.test(entry.ordinals)||bytes%3===1&&(alphabet64.indexOf(entry.ordinals.at(-1))&15)!==0||bytes%3===2&&(alphabet64.indexOf(entry.ordinals.at(-1))&3)!==0)throw Error('Repeating key lookup integrity failed.');
  lookupMap.set(entry.bankId,entry);
 }
 if(lookupMap.size!==Object.keys(LOOKUP_PINS).length)throw Error('Repeating key lookup integrity failed.');freeze(LOOKUP);freeze(LOOKUP_PINS);
 function sourceCycle(bank,entry,seedIndex){
  const cacheId=bank.id+'|'+seedIndex;if(cycles.has(cacheId))return cycles.get(cacheId);
  const seed=bank.seeds[seedIndex],n=seed.length,period=entry.periods[seedIndex],whole=bank.variant?.startsWith('rotate-')?n*n:bank.variant==='fold-repeat-endpoints'?2*n:bank.variant==='fold-skip-endpoints'?2*n-2:n;
  const value=i=>bank.variant==='rotate-left'?seed[(i%n+Math.floor(i/n))%n]:bank.variant==='rotate-right'?seed[(i%n-Math.floor(i/n)+n)%n]:bank.variant==='fold-repeat-endpoints'?seed[i<n?i:2*n-1-i]:bank.variant==='fold-skip-endpoints'?seed[i<n?i:2*n-2-i]:seed[i];
  if(!Number.isSafeInteger(whole)||whole<1||whole%period!==0||!bank.variant&&period!==n)throw Error('Repeating key lookup cycle integrity failed.');
  const cycle=Array.from({length:period},(_,i)=>value(i));for(let i=0;i<whole;i++)if(value(i)!==cycle[i%period])throw Error('Repeating key lookup cycle integrity failed.');
  freeze(cycle);cycles.set(cacheId,cycle);return cycle;
 }

 function list(){return freeze(DATA.banks.map(({seeds,...metadata})=>({...metadata,sourcePins:metadata.sourcePins.map(p=>({...p}))})));}
 function resolve(input){
  if(!exact(input,['bankId','bankSha256','start','count']))throw Error('Use an exact repeating key bank slice.');const {bankId,bankSha256,start,count}=input,bank=map.get(bankId);
  if(typeof bankId!=='string'||typeof bankSha256!=='string'||!bank||bank.sha256!==bankSha256||!Number.isSafeInteger(start)||!Number.isSafeInteger(count)||start<0||count<1||count>1024||start+count>bank.total)throw Error('Repeating key bank slice is outside its exact bounds.');
  const entry=lookupMap.get(bankId),out=[];
  for(let index=start;index<start+count;index++){const word=ordinal(entry,index),seedIndex=word>>>9,phase=word&511;if(word&32768||seedIndex>=bank.seeds.length||phase>=entry.periods[seedIndex])throw Error('Repeating key lookup ordinal integrity failed.');const cycle=sourceCycle(bank,entry,seedIndex);out.push(cycle.slice(phase).concat(cycle.slice(0,phase)));}
  return freeze(out);
 }
 const api=Object.freeze({list,resolve});if(typeof module==='object'&&module.exports)module.exports=api;else root.RepeatingKeyBanks=api;
})(typeof globalThis==='object'?globalThis:this);
'''


def files(root=ROOT):
    data = prepare(root)
    # Reuse the already reviewed small synchronous SHA256 implementation without
    # changing its existing sequence-bank owner or exposing an extra API.
    existing = (Path(root) / 'finite-sequence-banks.js').read_text(encoding='utf-8')
    helper = existing[existing.index(' function sha256(text){'):existing.index('\n const map=new Map();')]
    pins = {b['id']: b['sha256'] for b in data['banks']}
    lookup = lookup_index(data)
    lookup_pins = {entry['bankId']: entry['sha256'] for entry in lookup['entries']}
    header = "/* Generated source-pinned repeating keys. Build: python scripts/build_repeating_key_banks.py --write */\n(function(root){'use strict';\n const DATA=" + stable(data) + ',PINS=' + stable(pins) + ',LOOKUP=' + stable(lookup) + ',LOOKUP_PINS=' + stable(lookup_pins) + ';\n'
    stable_js = " const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);\n"
    return {'data/repeating-key-banks.json': stable(data) + '\n', 'data/repeating-key-bank-lookup.json': stable(lookup) + '\n', 'repeating-key-banks.js': header + stable_js + helper + RUNTIME}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true', help='Verify generated files without changing them (the default).')
    args = parser.parse_args()
    for name, content in files().items():
        path = ROOT / name
        if args.write:
            path.write_bytes(content.encode())
        elif not path.exists() or path.read_bytes() != content.encode():
            raise SystemExit('Stale generated file: ' + name)
    print('Verified 43 source keys, 309 ordinary rotations, and all four historical schedules (2561/2561/618/532). All 648 period-324 vectors retained as data; existing repeating-key execution bound remains 256. No output calculations.')


if __name__ == '__main__':
    main()
