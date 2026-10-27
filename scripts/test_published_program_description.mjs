/* Typed navigation descriptions only; no execution, evidence or data writes. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import Description from '../published-program-description.js';
import Navigation from '../published-program-discovery.js';
import {discovery} from './build_published_program_discovery.mjs';

let groups = 0;
async function test(name, fn) { await fn(); groups++; console.log('PASS ' + name); }

await test('genuine zero-step programs describe unchanged rune and separator positions', () => {
  const steps = [], before = JSON.stringify(steps);
  assert.equal(Description.program(steps), 'Keep all runes and separators in their original positions.');
  assert.equal(JSON.stringify(steps), before);
  assert.throws(() => Description.program(null));
  assert.throws(() => Description.program({}));
});

await test('all existing typed operations keep their exact prior step wording and ordered chain', () => {
  const steps = [
    {op: 'reverse', unit: 'line'}, {op: 'affine', a: 7, b: 0},
    {op: 'keyed-shift', mode: 'repeat', direction: 'subtract', reset: 'page', key: [1,2,3,4,5,6,7]},
    {op: 'keyed-shift', mode: 'plaintext-autokey', direction: 'add', reset: 'word', key: [1]},
    {op: 'keyed-shift', mode: 'ciphertext-autokey', direction: 'subtract', reset: 'line', key: [2]},
    {op: 'finite-shift', direction: 'add', reset: 'page', key: [1,2]},
    {op: 'interrupted-keyed-shift', direction: 'subtract', reset: 'line', key: [3], interrupts: [0]},
    {op: 'cumulative-difference', reset: 'word'}
  ];
  const before = JSON.stringify(steps);
  assert.equal(Description.program(steps), steps.map(Description.step).join(' → '));
  assert.equal(JSON.stringify(steps), before);
  assert.throws(() => Description.program([{op: 'unknown'}]));
});

await test('generator zero-step metadata passes the actual UI parser and renders an honest baseline label', async () => {
  // The directory validates pointer metadata, not evidence. This fixture varies
  // only its declared typed steps and performs no source fetch or proof claim.
  const catalog = JSON.parse(await readFile(new URL('../data/published-program-source-catalog.json', import.meta.url)));
  const pointer = {...catalog.entries[0], steps: []};
  const index = discovery({catalog: {schema: catalog.schema, entries: [pointer]},
    registry: {schema: 'liberpedia-published-program-evidence-v1', records: [], entries: []},
    records: [{id: pointer.recordId, status: 'published'}]});
  const parsed = Navigation.parse(index), group = parsed.groups[0], item = group.calculations[0];
  assert.equal(item.label, 'Setting 1 — keep original rune order');
  assert.equal(item.settings, Description.program([]));
  assert.deepEqual(item.reference, {recordId: pointer.recordId, caseId: pointer.caseId, revision: pointer.revision});
  const html = Navigation.render(group);
  assert(html.includes('keep original rune order'));
  assert(!html.includes('transform rune indices'));
});

await test('browser and Node export the same whole-program formatter without changing step API', async () => {
  const context = {};
  vm.runInNewContext(await readFile(new URL('../published-program-description.js', import.meta.url), 'utf8'), context);
  const browser = context.PublishedProgramDescription;
  assert.equal(browser.program([]), Description.program([]));
  assert.equal(browser.program([{op: 'reverse', unit: 'page'}]), Description.program([{op: 'reverse', unit: 'page'}]));
  assert.equal(typeof browser.step, 'function');
});

console.log(groups + ' typed published-program description groups passed; no target execution or metadata writes.');
