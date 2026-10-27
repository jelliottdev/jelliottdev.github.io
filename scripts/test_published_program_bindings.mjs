/* Build metadata only: no scientific inputs, calculations or source execution. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp, mkdir, readFile, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import E from '../local-experiment.js';
import * as B from './published_program_bindings.mjs';

const copy = structuredClone;
const pins = [{path: 'scripts/retained_program_output.mjs', sha256: 'a'.repeat(64)},
  {path: 'local-experiment.js', sha256: 'b'.repeat(64)}];
const ref = {recordId: 'invented-owner', revision: 'c'.repeat(64), caseId: 'setting--all-pages'};
const digest = value => createHash('sha256').update(E.stable(value)).digest('hex');
let groups = 0;
async function test(name, fn) { await fn(); groups++; console.log('PASS ' + name); }

await test('append sorts exact explicit pins and shares sets across arbitrary immutable references', () => {
  const input = copy(pins), first = B.append(B.empty(), ref, input);
  assert.deepEqual(first.sources[0].pins.map(pin => pin.path), ['local-experiment.js', 'scripts/retained_program_output.mjs']);
  assert.equal(first.sources[0].id, digest(first.sources[0].pins));
  assert.deepEqual(input, pins);
  const secondRef = {...ref, recordId: 'another-owner', revision: 'd'.repeat(64)};
  const second = B.append(first, secondRef, pins.toReversed());
  assert.equal(second.sources.length, 1);
  assert.equal(second.bindings.length, 2);
  assert.deepEqual(B.sourceFor(second, secondRef), first.sources[0].pins);
  assert.equal(B.sourceFor(second, {...ref, revision: 'e'.repeat(64)}), null);
  assert.deepEqual(B.append(second, ref, pins), second);
  assert(Object.isFrozen(second.sources[0].pins[0]));
});

await test('a new explicit code version gets a distinct set while old reference cannot be rebound', () => {
  const first = B.append(B.empty(), ref, pins), changed = copy(pins);
  changed[0].sha256 = 'f'.repeat(64);
  assert.throws(() => B.append(first, ref, changed), /immutable/);
  const next = B.append(first, {...ref, revision: 'e'.repeat(64)}, changed);
  assert.equal(next.sources.length, 2);
  assert.deepEqual(B.sourceFor(next, ref), first.sources[0].pins);
  assert.notDeepEqual(B.sourceFor(next, {...ref, revision: 'e'.repeat(64)}), first.sources[0].pins);
  assert.deepEqual(B.checkBaseline(next, first), next);
  assert.throws(() => B.checkBaseline(B.empty(), first), /removed or changed/);
  const oldOnly = B.append(B.empty(), {...ref, revision: 'e'.repeat(64)}, pins);
  assert.throws(() => B.checkBaseline(oldOnly, first), /bindings/);
});

await test('strict envelopes reject altered hashes orphan sets duplicate refs and malformed source paths', () => {
  const first = B.append(B.empty(), ref, pins);
  for (const mutate of [value => value.extra = true,
    value => value.sources.push(copy(value.sources[0])),
    value => value.bindings.push(copy(value.bindings[0])),
    value => value.sources[0].pins.reverse(),
    value => value.sources[0].pins[0].sha256 = 'f'.repeat(64),
    value => value.bindings[0].sourceId = '0'.repeat(64),
    value => value.bindings = []]) {
    const bad = copy(first); mutate(bad); assert.throws(() => B.validate(bad));
  }
  for (const path of ['../escape.js', '/absolute.js', 'scripts//empty.js', 'scripts/./dot.js', 'local-experiment.js\n'])
    assert.throws(() => B.append(B.empty(), ref, [{path, sha256: 'a'.repeat(64)}]));
  for (const patch of [{revision: ['c'.repeat(64)]}, {revision: 'c'.repeat(64) + '\n'},
    {caseId: 'case\n'}, {recordId: 'owner\n'}, {extra: true}])
    assert.throws(() => B.sourceFor(first, {...ref, ...patch}));
});

await test('capture is detached descriptor safe and rejects prototypes sparse arrays and mutation', () => {
  const first = B.append(B.empty(), ref, pins), mutable = copy(first), owned = B.validate(mutable);
  mutable.sources[0].pins[0].sha256 = 'f'.repeat(64);
  assert.deepEqual(owned, first);
  let reads = 0;
  const bad = copy(first);
  Object.defineProperty(bad.sources[0], 'pins', {enumerable: true, get() { reads++; return pins; }});
  assert.throws(() => B.validate(bad));
  const badRef = {...ref};
  Object.defineProperty(badRef, 'revision', {enumerable: true, get() { reads++; return ref.revision; }});
  assert.throws(() => B.append(first, badRef, pins));
  assert.equal(reads, 0);
  const sparse = copy(first); delete sparse.sources[0].pins[0]; assert.throws(() => B.validate(sparse));
  const unsafe = copy(first); Object.setPrototypeOf(unsafe, {unexpected: true}); assert.throws(() => B.validate(unsafe));
});

await test('all published reference and source count limits are strict without evicting retained sets', () => {
  const first = B.append(B.empty(), ref, pins);
  assert.throws(() => B.append(first, ref, []));
  assert.throws(() => B.append(first, ref, Array.from({length: 101}, (_, n) => ({path: 'file-' + n + '.js', sha256: 'a'.repeat(64)}))));
  assert.throws(() => B.append(first, ref, [pins[0], pins[0]]));
  const many = copy(first);
  many.bindings = Array.from({length: 1024}, (_, n) => ({...many.bindings[0], caseId: 'case-' + n}));
  assert.equal(B.validate(many).bindings.length, 1024);
  assert.throws(() => B.append(many, ref, pins), /manifest/);
  const sources = Array.from({length: 129}, (_, n) => {
    const values = [{path: 'file-' + n + '.js', sha256: 'a'.repeat(64)}];
    return {id: digest(values), pins: values};
  });
  assert.throws(() => B.validate({schema: B.SCHEMA, sources,
    bindings: sources.map((source, n) => ({...ref, caseId: 'case-' + n, sourceId: source.id}))}));
});

await test('CLI checks canonical retained metadata and baseline without writes or source evaluation', async () => {
  const root = await mkdtemp(join(tmpdir(), 'program-bindings-'));
  try {
    await mkdir(join(root, 'scripts'));
    await mkdir(join(root, 'data'));
    for (const path of ['scripts/published_program_bindings.mjs', 'local-experiment.js', 'finite-json.js'])
      await writeFile(join(root, path), await readFile(new URL('../' + path, import.meta.url)));
    const first = B.append(B.empty(), ref, pins), raw = E.stable(first) + '\n';
    await writeFile(join(root, B.PATH), raw);
    await writeFile(join(root, 'baseline.json'), raw);
    const cli = args => spawnSync(process.execPath, [join(root, 'scripts/published_program_bindings.mjs'), ...args],
      {encoding: 'utf8'});
    assert.equal(cli(['--check', '--baseline-manifest', join(root, 'baseline.json')]).status, 0);
    assert.equal(await readFile(join(root, B.PATH), 'utf8'), raw);
    assert.notEqual(cli(['--write']).status, 0);
    assert.notEqual(cli(['--check', '--baseline-manifest']).status, 0);
    await writeFile(join(root, B.PATH), E.stable(B.empty()) + '\n');
    assert.notEqual(cli(['--check', '--baseline-manifest', join(root, 'baseline.json')]).status, 0);
    await writeFile(join(root, B.PATH), '{"schema":0,"schema":"' + B.SCHEMA + '","sources":[],"bindings":[]}\n');
    assert.notEqual(cli(['--check']).status, 0);
  } finally {
    await rm(root, {recursive: true, force: true});
  }
});

console.log(groups + ' immutable declared program binding groups passed; no target or source execution.');
