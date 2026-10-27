/* Generic declared retained programs. No script execution or missing-output generation. */
import {readFile, writeFile, readdir, mkdir, stat, realpath, lstat} from 'node:fs/promises';
import {resolve, relative, dirname, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import E from '../local-experiment.js';
import J from '../finite-json.js';
import {validateRetainedProgramOutput} from './retained_program_output.mjs';
import * as Collection from './retained_program_collection.mjs';
import {checkedProgramIndex, checkProgramPointerReceipt} from '../services/idea-assistant/published-program-source-index.mjs';
import {readPublishedEvidence} from '../services/idea-assistant/published-evidence.mjs';

const ROOT = new URL('../', import.meta.url);
const MAX_BYTES = 8 * 1024 * 1024;
const CODE = [
  'scripts/build_declared_program_evidence.mjs',
  'scripts/retained_program_output.mjs',
  'local-experiment.js',
  'local-plan-controls.js',
  'finite-json.js',
  'computation-evidence.js',
  'services/idea-assistant/published-program-source-index.mjs',
  'published-numeric-bank-source.js'
];
const need = (value, message) => { if (!value) throw Error(message); };
const same = (a, b) => E.stable(a) === E.stable(b);
const sha = value => createHash('sha256')
  .update(typeof value === 'string' || value instanceof Uint8Array ? value : E.stable(value))
  .digest('hex');
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const slug = value => typeof value === 'string' && value.length <= 100
  && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
const pin = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const date = value => typeof value === 'string' && Number.isFinite(Date.parse(value))
  && new Date(value).toISOString() === value;
const capture = value => J.capture(value, {maxBytes: MAX_BYTES, maxDepth: 24, maxNodes: 500000});

function inside(base, target) {
  const path = relative(base, target);
  return !path.startsWith('..') && !isAbsolute(path);
}

function repositoryReader(base) {
  return async function bytes(path) {
    need(typeof path === 'string' && path.length <= 350 && /^[a-zA-Z0-9_./-]+$/.test(path)
      && !path.startsWith('/') && path.split('/').every(part => part && part !== '.' && part !== '..'),
    'Use a bounded repository file path');
    const target = await realpath(resolve(base, path));
    need(relative(base, target) && inside(base, target), 'Source path escaped the repository');
    need((await stat(target)).size <= MAX_BYTES, 'Source file exceeds its byte bound');
    return readFile(target);
  };
}

function declarationsFor(record) {
  const singles = record.published_programs || [];
  const collections = record.published_program_collections || [];
  for (const list of [singles, collections]) need(Array.isArray(list) && list.length <= 32,
    'Declare at most32 retained outputs or collections');
  need((!Object.hasOwn(record, 'published_programs') || singles.length > 0)
    && (!Object.hasOwn(record, 'published_program_collections') || collections.length > 0),
  'Published declarations cannot be empty');
  const declarations = [...singles, ...collections];
  need(declarations.length >= 1 && declarations.length <= 32
    && new Set(singles.map(item => item.id)).size === singles.length
    && new Set(declarations.map(item => item.output)).size === declarations.length,
  'Declare at most32 unique published programs');
  for (const declaration of declarations) validateDeclaration(record, declaration, collections.includes(declaration));
  return declarations.map(item => ({...item, collection: collections.includes(item)}));
}

function validateDeclaration(record, declaration, collection = false) {
  need(exact(declaration, [...(collection ? [] : ['id']), 'output', 'checked_at'])
    && (collection || typeof declaration.id === 'string' && declaration.id.length <= 80
    && /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?![\s\S])/.test(declaration.id))
    && date(declaration.checked_at) && typeof declaration.output === 'string'
    && declaration.output.length <= 300 && declaration.output.endsWith('.json')
    && !/\/(?:record|article)\.json$/.test(declaration.output)
    && declaration.output.startsWith('experiments/records/' + record.id + '/')
    && record.reproduction.outputs.filter(item => item.path === declaration.output).length === 1,
  'Published output must be a record-local pinned reproduction output');
}

async function reproductionSources(record, recordPath, declarations, bytes) {
  const rep = record.reproduction;
  need(rep && typeof rep.script === 'string' && pin(rep.script_sha256)
    && Array.isArray(rep.inputs) && Array.isArray(rep.outputs),
  'Published programs need pinned reproduction sources');
  for (const list of [rep.inputs, rep.outputs]) {
    need(new Set(list.map(item => item.path)).size === list.length, 'Duplicate reproduction source pins');
  }
  const pins = new Map(), retainedBytes = new Map();
  const sources = [{path: rep.script, sha256: rep.script_sha256}, ...rep.inputs, ...rep.outputs];
  for (const item of sources) {
    need(exact(item, ['path', 'sha256']), 'Use exact reproduction source pins');
    const {path, sha256} = item;
    need(pin(sha256), 'Invalid reproduction source hash');
    need(path !== recordPath && !/\/record\.json$/.test(path)
      && !path.startsWith('published-evidence/') && !/^data\/published/.test(path)
      && (!/^published-/.test(path) || CODE.includes(path)),
    'Published source pin would create a record or generated receipt cycle');
    // A dedicated script may also appear among the declared inputs, with the
    // same pin. Duplicate entries within either input/output list were rejected.
    need(!pins.has(path) || pins.get(path) === sha256, 'Conflicting reproduction source pins');
    pins.set(path, sha256);
    const raw = await bytes(path);
    need(sha(raw) === sha256, 'Reproduction source bytes changed: ' + path);
    if (declarations.some(declaration => declaration.output === path)) retainedBytes.set(path, raw);
  }
  return {pins, retainedBytes};
}

function validateOwnerScope(record, task, official) {
  need(same(task.alphabet, official.alphabet), 'Retained program alphabet differs from official inputs');
  const pages = record.scope?.pages;
  need(Array.isArray(pages) && pages.length > 0 && new Set(pages).size === pages.length
    && same(task.pages.map(page => page.id), pages.filter(id => task.pages.some(page => page.id === id))),
  'Retained program pages differ from the ordered owner scope');
}

async function projectionSourcePins(task, scientificPins, officialPages, bytes, collection = false) {
  const pins = new Map(scientificPins);
  for (const path of [...CODE, ...(collection ? ['scripts/retained_program_collection.mjs'] : [])]) {
    const hash = sha((await bytes(path)).toString('utf8').replaceAll('\r\n', '\n'));
    need(!pins.has(path) || pins.get(path) === hash, 'Maintained code pin conflicts with reproduction bytes');
    pins.set(path, hash);
  }
  for (const page of task.pages) {
    need(officialPages.has(page.id) && officialPages.get(page.id) === page.text,
      'Retained page differs from official raw text');
    const path = 'text/' + page.id + '.txt', raw = await bytes(path);
    need(raw.toString('utf8') === page.text, 'Retained page differs from pinned text source');
    if (pins.has(path)) need(pins.get(path) === sha(raw), 'Official text pin changed');
    pins.set(path, sha(raw));
  }
  need(pins.size <= 100, 'Published provenance exceeds100 source pins');
  return [...pins].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
    .map(([path, sha256]) => ({path, sha256}));
}

// Preserve the original public reference when a publisher implementation changes
// but the exact retained calculation, date and scientific source bytes do not.
// The old envelope is revalidated; it is never trusted merely for being on disk.
async function preserveExistingProjection(record, declaration, retained, sourcePins, previous, bytes) {
  const pointer = previous.find(item => item.recordId === record.id
    && item.caseId === declaration.id + '--all-pages');
  if (!pointer) return null;
  need(pointer.path === 'published-evidence/programs/declared-' + pointer.revision + '.json',
    'Existing declared receipt lost its content-addressed path');
  const raw = await bytes(pointer.path);
  need(raw.length === pointer.bytes && sha(raw) === pointer.sha256,
    'Immutable declared receipt collision: existing published receipt bytes changed');
  const envelope = JSON.parse(raw);
  const checked = await readPublishedEvidence({recordId: pointer.recordId, revision: pointer.revision,
    caseId: pointer.caseId, registry: envelope, history: null, programIndex: null});
  need(checked, 'Existing published receipt could not be verified');
  checkProgramPointerReceipt(pointer, {...checked, source: {task: checked.task, run: checked.run,
    inputVersion: checked.inputVersion}});
  const maintained = new Set([...CODE, 'scripts/retained_program_collection.mjs']);
  const scientific = pins => pins.filter(pin => !maintained.has(pin.path));
  if (!same(checked.task, retained.task) || !same(checked.run, retained.run)
    || !same(scientific(checked.provenance.sourcePins), scientific(sourcePins))) return null;
  // Metadata cannot redirect an otherwise valid retained source to another task.
  const projection = checked.provenance.projection;
  need(projection.ownerRecordId === record.id && projection.sourceProgramId === declaration.id
    && pointer.taskId === retained.task.taskId && pointer.resultId === retained.run.id,
    'Existing published pointer changed its declared calculation');
  return {path: pointer.path, text: raw.toString('utf8'), pointer};
}

function publishedProjection(record, declaration, retained, sourcePins) {
  const task = retained.task;
  const projection = {
    id: declaration.id, ownerRecordId: record.id, sourceProgramId: declaration.id,
    inputVersion: 'raw', steps: task.steps, criterion: task.criterion,
    pages: task.pages.map(page => page.id), alphabetSha256: sha(task.alphabet),
    taskId: task.taskId, resultId: retained.run.id
  };
  const provenance = {
    schema: 'liberpedia-published-program-projection-v1', recordId: record.id,
    projection, sourcePins, checkedAt: declaration.checked_at,
    dateMeaning: 'Date recorded for the retained output or its explicit import and verification; not an authenticated historical execution timestamp, browser submission or the current loading time.',
    verificationMeaning: 'The retained output was verified against the exact fixed program and independent synthetic implementation controls. This does not establish a decryption. Maintained verifier code pins use UTF-8 with LF line endings; scientific source pins use exact bytes.'
  };
  const revision = sha(provenance);
  const entry = {
    recordId: record.id, revision, caseId: declaration.id + '--all-pages',
    task, inputVersion: 'raw', run: retained.run
  };
  const envelope = {
    schema: 'liberpedia-published-program-evidence-v1',
    records: [{recordId: record.id, revision, provenance}], entries: [entry]
  };
  const text = E.stable(envelope) + '\n';
  const path = 'published-evidence/programs/declared-' + revision + '.json';
  need(Buffer.byteLength(text) <= MAX_BYTES, 'Published receipt exceeds its byte bound');
  const pointer = {
    recordId: record.id, revision, caseId: entry.caseId, inputVersion: 'raw',
    taskId: task.taskId, resultId: retained.run.id, createdAt: declaration.checked_at,
    steps: task.steps, criterion: task.criterion, alphabetSha256: projection.alphabetSha256,
    pages: task.pages.map(page => ({id: page.id, textSha256: sha(page.text)})),
    path, sha256: sha(text), bytes: Buffer.byteLength(text)
  };
  return {path, text, pointer};
}

export async function prepare({root = ROOT} = {}) {
  const base = await realpath(root instanceof URL ? fileURLToPath(root) : resolve(root));
  const bytes = repositoryReader(base);
  const official = JSON.parse(await bytes('data/local-run-inputs.json'));
  need(official.schema === 'liberpedia-local-inputs-v1' && Array.isArray(official.pages)
    && Array.isArray(official.alphabet), 'Official raw input bundle is malformed');
  const officialPages = new Map(official.pages.map(page => [page.id, page.raw]));
  const files = new Map(), entries = [];
  let previous = [];
  try { previous = checkedProgramIndex(JSON.parse(await bytes('data/published-declared-program-source-index.json'))).entries; }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const folders = (await readdir(resolve(base, 'experiments/records'), {withFileTypes: true}))
    .filter(item => item.isDirectory()).map(item => item.name).sort();
  for (const folder of folders) {
    const recordPath = 'experiments/records/' + folder + '/record.json';
    const recordBytes = await bytes(recordPath).catch(error => {
      if (error.code === 'ENOENT') return null;
      throw error;
    });
    // Some historical reproduction folders have no canonical record source.
    if (recordBytes === null) continue;
    const record = capture(JSON.parse(recordBytes));
    if (!Object.hasOwn(record, 'published_programs') && !Object.hasOwn(record, 'published_program_collections')) continue;
    need(['published', 'draft'].includes(record.status) && record.id === folder && slug(record.id),
      'Only canonical published or draft owners may declare programs');
    // Withdrawal removes active pointers but never deletes retained receipts.
    if (record.status === 'draft') continue;
    const declarations = declarationsFor(record);
    const sources = await reproductionSources(record, recordPath, declarations, bytes);
    const identifiers = new Set();
    for (const declaration of declarations) {
      // Parse the same detached bytes whose reproduction hash was checked.
      const raw = JSON.parse(sources.retainedBytes.get(declaration.output));
      const handle = declaration.collection ? Collection.prepare(raw) : null;
      const members = handle ? Collection.inspect(handle).programs : [{id: declaration.id}];
      for (const member of members) {
      need(!identifiers.has(member.id) && identifiers.size < 128, 'Repeated or excessive retained programs on one owner');
      identifiers.add(member.id);
      const selected = {...declaration, id: member.id};
      const retained = handle ? await Collection.hydrate(handle, member.id)
        : await validateRetainedProgramOutput(raw);
      need(declaration.checked_at === retained.run.createdAt,
        'Declaration date must equal the retained calculation date');
      validateOwnerScope(record, retained.task, official);
      const sourcePins = await projectionSourcePins(retained.task, sources.pins, officialPages, bytes, declaration.collection);
      const published = await preserveExistingProjection(record, selected, retained, sourcePins, previous, bytes)
        || publishedProjection(record, selected, retained, sourcePins);
      files.set(published.path, published.text);
      entries.push(published.pointer);
      }
    }
  }
  const index = checkedProgramIndex({schema: 'liberpedia-published-program-source-index-v1', entries});
  files.set('data/published-declared-program-source-index.json', E.stable(index) + '\n');
  return {root: base, files, index};
}

async function containedDestination(base, target) {
  need(inside(base, await realpath(target)), 'Generated destination escaped the repository');
}

async function writeOrCheck(base, path, text, write) {
  const target = resolve(base, path);
  let ancestor = dirname(target);
  while (true) {
    try {
      await containedDestination(base, ancestor);
      break;
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      const parent = dirname(ancestor);
      need(parent !== ancestor, 'Generated destination has no repository ancestor');
      ancestor = parent;
    }
  }
  if (!write) {
    await containedDestination(base, target);
    need(await readFile(target, 'utf8') === text, 'Declared published program artifact is stale: ' + path);
    return;
  }
  await mkdir(dirname(target), {recursive: true});
  await containedDestination(base, dirname(target));
  try {
    need(!(await lstat(target)).isSymbolicLink(), 'Generated destination cannot be a symbolic link');
    await containedDestination(base, target);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  if (/^published-evidence\/programs\/declared-[a-f0-9]{64}\.json$/.test(path)) {
    // A content-addressed receipt is an immutable historical artifact. Repairing
    // a conflicting file requires investigation, never silent regeneration.
    try {
      const existing = await readFile(target);
      need(existing.equals(Buffer.from(text)), 'Immutable declared receipt collision: ' + path);
      return;
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    try {
      await writeFile(target, text, {flag: 'wx'});
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      need((await readFile(target)).equals(Buffer.from(text)), 'Immutable declared receipt collision: ' + path);
    }
    return;
  }
  await writeFile(target, text);
}

export async function build({root = ROOT, write = false} = {}) {
  const result = await prepare({root});
  for (const [path, text] of result.files) await writeOrCheck(result.root, path, text, write);
  return result;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const flags = process.argv.slice(2);
  need(flags.length <= 1 && flags.every(flag => ['--write', '--check'].includes(flag)), 'Use --write or --check');
  const result = await build({write: flags.includes('--write')});
  console.log('PASS ' + result.index.entries.length + ' declared retained programs; no scripts or missing outputs executed');
}
