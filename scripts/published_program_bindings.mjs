/* Build-only explicit reproduction pin roles; no evidence or runtime authority. */
import {createHash} from 'node:crypto';
import {readFile, stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import E from '../local-experiment.js';
import J from '../finite-json.js';

export const PATH = 'data/published-declared-program-bindings.json';
export const SCHEMA = 'liberpedia-declared-program-bindings-v1';
export const LIMITS = Object.freeze({bytes: 4 * 1024 * 1024, bindings: 1024, sources: 128, pins: 100});
const need = (condition, message) => { if (!condition) throw Error(message); };
const same = (a, b) => E.stable(a) === E.stable(b);
const sha = value => createHash('sha256').update(E.stable(value)).digest('hex');
const exact = (value, fields) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === fields.length && fields.every(field => Object.hasOwn(value, field));
const hex = value => typeof value === 'string' && /^[a-f0-9]{64}(?![\s\S])/.test(value);
const safePath = value => typeof value === 'string' && value.length <= 350
  && /^[A-Za-z0-9_./-]+(?![\s\S])/.test(value)
  && value.split('/').every(part => part && part !== '.' && part !== '..');
const capture = value => J.capture(value, {maxBytes: LIMITS.bytes, maxDepth: 8, maxNodes: 60000});
function freeze(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}

function checkedRef(ref) {
  need(exact(ref, ['recordId', 'revision', 'caseId'])
    && typeof ref.recordId === 'string' && ref.recordId.length <= 100
    && /^[a-z0-9]+(?:-[a-z0-9]+)*(?![\s\S])/.test(ref.recordId)
    && typeof ref.caseId === 'string' && ref.caseId.length <= 200
    && /^[a-z0-9-]+(?![\s\S])/.test(ref.caseId) && hex(ref.revision),
  'Use an exact published program reference');
  return ref;
}

function checkedPins(pins, sorted = true) {
  need(Array.isArray(pins) && pins.length > 0 && pins.length <= LIMITS.pins,
    'Use a bounded nonempty explicit reproduction pin set');
  const seen = new Set();
  let previous = null;
  for (const pin of pins) {
    need(exact(pin, ['path', 'sha256']) && safePath(pin.path) && hex(pin.sha256)
      && !seen.has(pin.path), 'Invalid or repeated explicit reproduction pin');
    if (sorted && previous !== null) need(previous < pin.path, 'Explicit reproduction pins must be sorted');
    previous = pin.path;
    seen.add(pin.path);
  }
  return pins;
}

export function empty() {
  return freeze({schema: SCHEMA, sources: [], bindings: []});
}

export function validate(input) {
  const value = capture(input);
  need(exact(value, ['schema', 'sources', 'bindings']) && value.schema === SCHEMA
    && Array.isArray(value.sources) && value.sources.length <= LIMITS.sources
    && Array.isArray(value.bindings) && value.bindings.length <= LIMITS.bindings,
  'Invalid declared program bindings manifest');
  const sources = new Map(), used = new Set(), refs = new Set();
  for (const source of value.sources) {
    need(exact(source, ['id', 'pins']) && hex(source.id) && !sources.has(source.id),
      'Invalid or repeated explicit source set');
    checkedPins(source.pins);
    need(sha(source.pins) === source.id, 'Explicit source set hash changed');
    sources.set(source.id, source);
  }
  for (const binding of value.bindings) {
    need(exact(binding, ['recordId', 'revision', 'caseId', 'sourceId']), 'Invalid program source binding');
    const ref = checkedRef({recordId: binding.recordId, revision: binding.revision, caseId: binding.caseId});
    const key = E.stable(ref);
    need(hex(binding.sourceId) && sources.has(binding.sourceId) && !refs.has(key),
      'Unknown source set or repeated published reference');
    refs.add(key);
    used.add(binding.sourceId);
  }
  need(used.size === sources.size, 'Explicit source sets cannot be orphaned');
  return freeze(value);
}

export function sourceFor(manifest, reference) {
  const value = validate(manifest), ref = checkedRef(capture(reference));
  const binding = value.bindings.find(item => item.recordId === ref.recordId
    && item.revision === ref.revision && item.caseId === ref.caseId);
  return binding ? value.sources.find(item => item.id === binding.sourceId).pins : null;
}

export function append(manifest, reference, explicitPins) {
  const value = validate(manifest), ref = checkedRef(capture(reference));
  const pins = checkedPins(capture(explicitPins), false).sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  const sourceId = sha(pins);
  const existing = value.bindings.find(item => item.recordId === ref.recordId
    && item.revision === ref.revision && item.caseId === ref.caseId);
  if (existing) {
    need(existing.sourceId === sourceId, 'An existing program binding is immutable');
    return value;
  }
  return validate({schema: SCHEMA,
    sources: value.sources.some(item => item.id === sourceId)
      ? value.sources : [...value.sources, {id: sourceId, pins}],
    bindings: [...value.bindings, {...ref, sourceId}]});
}

export function checkBaseline(current, previous) {
  const value = validate(current), baseline = validate(previous);
  for (const source of baseline.sources) need(value.sources.some(item => same(item, source)),
    'Retained explicit source sets may not be removed or changed');
  for (const binding of baseline.bindings) need(value.bindings.some(item => same(item, binding)),
    'Retained program bindings may not be removed or changed');
  return value;
}

async function readBounded(path) {
  need((await stat(path)).size <= LIMITS.bytes, 'Bindings file exceeds its byte bound');
  const raw = await readFile(path);
  need(raw.length <= LIMITS.bytes, 'Bindings file exceeds its byte bound');
  const text = new TextDecoder('utf-8', {fatal: true}).decode(raw);
  // Repeated fields cannot be faithfully represented by JSON.parse. Canonical
  // generated bytes are required at this external CLI boundary.
  const value = validate(JSON.parse(text));
  need(text === E.stable(value) + '\n', 'Bindings file must use canonical JSON bytes');
  return value;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    need(args[0] === '--check' && (args.length === 1
      || args.length === 3 && args[1] === '--baseline-manifest'),
    'Use --check [--baseline-manifest file]');
    const current = await readBounded(new URL('../' + PATH, import.meta.url));
    if (args.length === 3) checkBaseline(current, await readBounded(resolve(args[2])));
    console.log('CHECKED ' + current.bindings.length + ' immutable declared program bindings');
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
