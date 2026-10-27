/* Build-only immutable declared pointers, separate from active discovery. */
import {createHash} from 'node:crypto';
import {readFile, realpath, stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve, relative, isAbsolute} from 'node:path';
import E from '../local-experiment.js';
import {checkedProgramIndex, checkProgramPointerReceipt} from '../services/idea-assistant/published-program-source-index.mjs';
import {readPublishedEvidence} from '../services/idea-assistant/published-evidence.mjs';

export const PATH = 'data/published-declared-program-history.json';
export const SCRIPT_PATH = 'published-declared-program-history-data.js';
export const SCHEMA = 'liberpedia-published-program-source-index-v1';
export const LIMITS = Object.freeze({bytes: 4 * 1024 * 1024, entries: 1024});
const ROOT = fileURLToPath(new URL('../', import.meta.url));
const need = (condition, message) => { if (!condition) throw Error(message); };
const key = value => [value.recordId, value.revision, value.caseId].join('|');
const same = (a, b) => E.stable(a) === E.stable(b);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export function empty() {
  return validate({schema: SCHEMA, entries: []});
}

export function validate(input) {
  const history = checkedProgramIndex(input);
  for (const pointer of history.entries) need(!Object.hasOwn(pointer, 'sourceFormat')
    && pointer.path === 'published-evidence/programs/declared-' + pointer.revision + '.json',
  'History retains only exact content-addressed declared program receipts');
  return history;
}

export function append(history, pointers) {
  const previous = validate(history), added = validate({schema: SCHEMA, entries: pointers});
  const entries = new Map(previous.entries.map(pointer => [key(pointer), pointer]));
  for (const pointer of added.entries) {
    const old = entries.get(key(pointer));
    need(!old || same(old, pointer), 'An immutable declared program pointer changed');
    if (!old) entries.set(key(pointer), pointer);
  }
  return validate({schema: SCHEMA, entries: [...entries.values()]});
}

export function checkBaseline(current, baseline) {
  const history = validate(current), previous = validate(baseline);
  const entries = new Map(history.entries.map(pointer => [key(pointer), pointer]));
  for (const pointer of previous.entries) need(same(entries.get(key(pointer)), pointer),
    'Retained declared pointers may not be removed or changed');
  return history;
}

export function script(history) {
  const data = E.stable(validate(history));
  return "/* Generated retained declared references; never active discovery. */\n"
    + "(function(root){'use strict';const data=" + data
    + ";function freeze(v){if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}freeze(data);if(typeof module==='object'&&module.exports)module.exports=data;else root.PublishedDeclaredProgramHistoryData=data;})(typeof globalThis!=='undefined'?globalThis:this);\n";
}

async function bytes(root, name, limit) {
  const base = await realpath(root), path = await realpath(resolve(base, name));
  const local = relative(base, path);
  need(local && !local.startsWith('..') && !isAbsolute(local), 'Retained receipt path escapes repository');
  need((await stat(path)).size <= limit, 'Retained metadata exceeds its byte bound');
  const raw = await readFile(path);
  need(raw.length <= limit, 'Retained metadata exceeds its byte bound');
  return raw;
}

export async function checkReceipts(input, {root = ROOT} = {}) {
  const history = validate(input);
  for (const pointer of history.entries) {
    const raw = await bytes(root, pointer.path, pointer.bytes);
    need(raw.length === pointer.bytes && sha(raw) === pointer.sha256,
      'Retained declared receipt bytes changed');
    const registry = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(raw));
    const source = await readPublishedEvidence({recordId: pointer.recordId, revision: pointer.revision,
      caseId: pointer.caseId, registry, programIndex: null, history: null});
    need(source, 'Retained declared receipt is absent from its envelope');
    checkProgramPointerReceipt(pointer, {publishedSource: source.publishedSource,
      provenance: source.provenance, source: {task: source.task, run: source.run, inputVersion: source.inputVersion}});
  }
  return history;
}

async function readManifest(path) {
  need((await stat(path)).size <= LIMITS.bytes, 'Declared history exceeds its byte bound');
  const raw = await readFile(path);
  need(raw.length <= LIMITS.bytes, 'Declared history exceeds its byte bound');
  const text = new TextDecoder('utf-8', {fatal: true}).decode(raw), history = validate(JSON.parse(text));
  need(text === E.stable(history) + '\n', 'Declared history must use canonical JSON bytes');
  return history;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    need(args[0] === '--check' && (args.length === 1 || args.length === 3 && args[1] === '--baseline-manifest'),
      'Use --check [--baseline-manifest file]');
    const history = await readManifest(resolve(ROOT, PATH));
    if (args.length === 3) checkBaseline(history, await readManifest(resolve(args[2])));
    need((await bytes(ROOT, SCRIPT_PATH, LIMITS.bytes + 1024)).equals(Buffer.from(script(history))),
      'Generated declared history module is stale');
    await checkReceipts(history);
    console.log('CHECKED ' + history.entries.length + ' immutable declared program references');
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
