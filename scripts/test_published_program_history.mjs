/* Pointer history only; existing retained proofs are verified, never generated. */
import assert from 'node:assert/strict';
import {readFile, writeFile, mkdtemp, mkdir, rm} from 'node:fs/promises';
import {join, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import vm from 'node:vm';
import E from '../local-experiment.js';
import * as H from './published_program_history.mjs';

const active = JSON.parse(await readFile(new URL('../data/published-declared-program-source-index.json', import.meta.url)));
assert(active.entries.length > 0);
const pointer = active.entries[0], copy = structuredClone;
let groups = 0;
async function test(name, fn) { await fn(); groups++; console.log('PASS ' + name); }

await test('withdrawal and revisions retain exact immutable pointers without entering the active index', () => {
  const original = copy(active), first = H.append(H.empty(), [pointer]);
  const second = {...pointer, revision: 'e'.repeat(64), path: 'published-evidence/programs/declared-' + 'e'.repeat(64) + '.json'};
  const history = H.append(first, [second]);
  assert.equal(history.entries.length, 2);
  assert.deepEqual(history.entries[0], pointer);
  assert.deepEqual(H.append(history, []), history);
  assert.deepEqual(H.append(history, [pointer]), history);
  assert.deepEqual(H.checkBaseline(history, first), history);
  assert.deepEqual(active, original);
  assert(Object.isFrozen(history.entries[0].pages[0]));
  assert.throws(() => H.append(first, [{...pointer, createdAt: '2020-01-01T00:00:00.000Z'}]), /immutable/);
  assert.throws(() => H.checkBaseline(H.empty(), first), /removed or changed/);
});

await test('whole pointer metadata identity is immutable and unsupported providers cannot enter declared history', () => {
  const first = H.append(H.empty(), [pointer]);
  for (const patch of [{taskId: '0'.repeat(64)}, {sha256: '0'.repeat(64)}, {bytes: pointer.bytes + 1},
    {path: '../escape.json'}, {path: 'published-evidence/programs/not-declared.json'},
    {sourceFormat: 'numeric-bank-matrix-v1', programId: 'invented'}, {extra: true}]) {
    assert.throws(() => H.append(first, [{...pointer, ...patch}]));
  }
  assert.throws(() => H.validate({schema: H.SCHEMA, entries: [pointer, pointer]}));
  assert.throws(() => H.validate({schema: H.SCHEMA, entries: [], extra: true}));
});

await test('captures are detached and getter/sparse/prototype inputs never become retained authority', () => {
  const original = {schema: H.SCHEMA, entries: [copy(pointer)]}, detached = H.validate(original);
  original.entries[0].pages[0].textSha256 = '0'.repeat(64);
  assert.deepEqual(detached.entries[0], pointer);
  let calls = 0;
  const hostile = {schema: H.SCHEMA};
  Object.defineProperty(hostile, 'entries', {enumerable: true, get() { calls++; return [pointer]; }});
  assert.throws(() => H.validate(hostile));
  assert.equal(calls, 0);
  const sparse = {schema: H.SCHEMA, entries: [copy(pointer)]}; delete sparse.entries[0];
  assert.throws(() => H.validate(sparse));
  assert.throws(() => H.validate(Object.setPrototypeOf({schema: H.SCHEMA, entries: []}, {extra: true})));
});

await test('the fixed1024 history limit rejects growth rather than deleting old references', () => {
  const pointers = Array.from({length: 1024}, (_, n) => {
    const revision = n.toString(16).padStart(64, '0');
    return {...pointer, pages: [pointer.pages[0]], revision, path: 'published-evidence/programs/declared-' + revision + '.json'};
  });
  const full = H.append(H.empty(), pointers);
  assert.equal(full.entries.length, 1024);
  assert.throws(() => H.append(full, [{...pointer, revision: 'f'.repeat(64), path: 'published-evidence/programs/declared-' + 'f'.repeat(64) + '.json'}]));
  assert.equal(full.entries.length, 1024);
});

await test('generated browser and CommonJS modules expose the same deeply frozen read-only history', () => {
  const history = H.append(H.empty(), [pointer]), text = H.script(history), browser = {};
  vm.runInNewContext(text, browser);
  assert.equal(E.stable(browser.PublishedDeclaredProgramHistoryData), E.stable(history));
  assert(Object.isFrozen(browser.PublishedDeclaredProgramHistoryData.entries[0].steps));
  const node = {module: {exports: {}}}; vm.runInNewContext(text, node);
  assert.equal(E.stable(node.module.exports), E.stable(history));
});

await test('retained proof bytes and pointer metadata are independently checked even after withdrawal', async () => {
  const root = await mkdtemp(join(tmpdir(), 'program-history-'));
  try {
    const target = join(root, pointer.path);
    await mkdir(dirname(target), {recursive: true});
    const raw = await readFile(new URL('../' + pointer.path, import.meta.url));
    await writeFile(target, raw);
    const history = H.append(H.empty(), [pointer]);
    assert.deepEqual(await H.checkReceipts(history, {root}), history);
    const drift = {...pointer, taskId: '0'.repeat(64)};
    await assert.rejects(H.checkReceipts(H.append(H.empty(), [drift]), {root}), /metadata/);
    await writeFile(target, raw.subarray(0, raw.length - 1));
    await assert.rejects(H.checkReceipts(history, {root}), /bytes changed/);
    await rm(target);
    await assert.rejects(H.checkReceipts(history, {root}));
  } finally {
    await rm(root, {recursive: true, force: true});
  }
});

console.log(groups + ' immutable declared program history groups passed; no new scientific outputs.');
