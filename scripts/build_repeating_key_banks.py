"""Pin source keys and bounded distinct rotation domains; never compute target output.

Ordering is numeric lexicographic over complete index vectors, with a shorter
prefix first. Exact duplicates are removed; cyclic-equivalent vectors of
different starting places remain separate unless their complete vectors match.
Arithmetic direction is not a key: 309 rotations give 618 two-sign settings.
"""
import argparse
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
    if bank['rule'] in ('fold-repeat-endpoints-v1', 'fold-skip-endpoints-v1'):
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
    for variant, label in [('fold-repeat-endpoints', 'Historical folded keys — repeat endpoints'), ('fold-skip-endpoints', 'Historical folded keys — skip endpoints')]:
        bank = dict(id='public-wordlist-' + variant + '-v1', label=label, rule=variant + '-v1', total=expected[variant], sourcePins=[dict(path=p, sha256=h) for p, h in sorted({**PINS, **SCHEDULE_PINS}.items())], seeds=[list(k) for k in seeds], historicalSettings=expected[variant], variant=variant, sourceAudit=audit)
        if len(vectors(bank)) != bank['total'] or any(len(k) > 256 for k in vectors(bank)):
            raise ValueError('The named folded variant cannot fit the unchanged repeating key limit')
        bank['sha256'] = digest(bank)
        banks.append(bank)
    return dict(schema=SCHEMA, banks=banks)


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
 const compare=(a,b)=>{for(let i=0;i<Math.min(a.length,b.length);i++)if(a[i]!==b[i])return a[i]-b[i];return a.length-b.length;},cache=new Map(),map=new Map();
 for(const bank of DATA.banks){const {sha256:pin,...basis}=bank,folded=Object.hasOwn(bank,'variant');if(!exact(bank,['id','label','rule','total','sourcePins','seeds','historicalSettings','sha256',...(folded?['variant','sourceAudit']:[])])||map.has(bank.id)||PINS[bank.id]!==pin||sha256(stable(basis))!==pin||!['source-keys-v1','all-rotations-v1','fold-repeat-endpoints-v1','fold-skip-endpoints-v1'].includes(bank.rule)||!Number.isSafeInteger(bank.total)||bank.total<1||!Array.isArray(bank.seeds)||bank.seeds.length!==43||bank.seeds.some(k=>!Array.isArray(k)||!k.length||k.length>256||k.some(n=>!Number.isInteger(n)||n<0||n>28)))throw Error('Repeating key bank integrity failed.');map.set(bank.id,bank);}
 if(DATA.schema!=='liberpedia-repeating-key-banks-v1'||map.size!==Object.keys(PINS).length||map.size<1)throw Error('The repeating key bank set changed.');freeze(DATA);freeze(PINS);
 function list(){return freeze(DATA.banks.map(({seeds,...metadata})=>({...metadata,sourcePins:metadata.sourcePins.map(p=>({...p}))})));}
 function resolve(input){
  if(!exact(input,['bankId','bankSha256','start','count']))throw Error('Use an exact repeating key bank slice.');const {bankId,bankSha256,start,count}=input,bank=map.get(bankId);
  if(typeof bankId!=='string'||typeof bankSha256!=='string'||!bank||bank.sha256!==bankSha256||!Number.isSafeInteger(start)||!Number.isSafeInteger(count)||start<0||count<1||count>1024||start+count>bank.total)throw Error('Repeating key bank slice is outside its exact bounds.');
  let keys=cache.get(bankId);if(!keys){const candidates=[];for(const key of bank.seeds){if(bank.rule==='source-keys-v1')candidates.push(key.slice());else{let cycle=key;if(bank.rule.startsWith('fold-')){const whole=bank.variant==='fold-repeat-endpoints'?key.concat(key.slice().reverse()):key.concat(key.slice(1,-1).reverse());for(let n=1;n<=whole.length;n++)if(whole.length%n===0&&whole.every((v,i)=>v===whole[i%n])){cycle=whole.slice(0,n);break;}}for(let phase=0;phase<cycle.length;phase++)candidates.push(cycle.slice(phase).concat(cycle.slice(0,phase)));}}const unique=new Map(candidates.map(key=>[key.join(','),key]));keys=[...unique.values()].sort(compare);if(keys.length!==bank.total||keys.some(k=>k.length>256))throw Error('The repeating key vector count or length changed.');freeze(keys);cache.set(bankId,keys);}
  return freeze(keys.slice(start,start+count).map(key=>key.slice()));
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
    header = "/* Generated source-pinned repeating keys. Build: python scripts/build_repeating_key_banks.py --write */\n(function(root){'use strict';\n const DATA=" + stable(data) + ',PINS=' + stable(pins) + ';\n'
    stable_js = " const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);\n"
    return {'data/repeating-key-banks.json': stable(data) + '\n', 'repeating-key-banks.js': header + stable_js + helper + RUNTIME}


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
    print('Verified 43 archived keys, 309 rotations, and exact folded variants 618/532; full historical schedule census 6272 includes 648 unsupported period-324 vectors. No output calculations.')


if __name__ == '__main__':
    main()
