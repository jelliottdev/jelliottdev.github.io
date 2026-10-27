/* Offline shared packing for complete retained programs. No source execution.
 * Hydration verifies one supplied saved output; it never fills missing values. */
import {readFile, stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import E from '../local-experiment.js';
import J from '../finite-json.js';
import {prepareRetainedRuneOutputs} from './retained_program_output.mjs';
import {validateProgramCriterion} from '../services/idea-assistant/published-program-source-index.mjs';

export const SCHEMA = 'liberpedia-retained-program-collection-v1';
export const LIMITS = Object.freeze({bytes: 8 * 1024 * 1024, nodes: 2000000, depth: 24, programs: 128});
const handles = new WeakMap();
const need = (value, message) => { if (!value) throw Error(message); };
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const same = (a, b) => E.stable(a) === E.stable(b);
const date = value => typeof value === 'string' && Number.isFinite(Date.parse(value))
  && new Date(value).toISOString() === value;
const freeze = value => {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
};

function taskFor(collection, program) {
  return {
    schema: E.TASK, engine: E.ENGINE, taskId: program.taskId, title: program.title,
    alphabet: collection.alphabet, pages: collection.pages, steps: program.steps,
    criterion: collection.criterion
  };
}

function validateProgram(collection, program, runeCounts) {
  need(exact(program, ['id', 'taskId', 'title', 'steps', 'outputs', 'controls', 'createdAt'])
    && typeof program.id === 'string' && program.id.length <= 80
    && /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?![\s\S])/.test(program.id)
    && date(program.createdAt), 'Use exact named retained collection programs');
  E.validateTask(taskFor(collection, program));
  need(Array.isArray(program.outputs) && program.outputs.length === collection.pages.length,
    'Each retained program needs one full saved vector per declared page');
  for (let index = 0; index < collection.pages.length; index++) {
    const output = program.outputs[index];
    need(exact(output, ['page', 'values']) && output.page === collection.pages[index].id
      && Array.isArray(output.values) && output.values.length === runeCounts[index]
      && output.values.every(value => Number.isInteger(value) && value >= 0 && value < 29),
    'Retained collection output page order, length or values changed');
  }
}

export function prepare(input) {
  // This new aggregate budget applies only to the packed collection. Hydrated
  // programs still pass the existing single-program limits without exceptions.
  const value = J.capture(input, {maxBytes: LIMITS.bytes, maxDepth: LIMITS.depth, maxNodes: LIMITS.nodes});
  need(exact(value, ['schema', 'inputVersion', 'alphabet', 'pages', 'criterion', 'programs'])
    && value.schema === SCHEMA && value.inputVersion === 'raw'
    && Array.isArray(value.programs) && value.programs.length >= 1
    && value.programs.length <= LIMITS.programs, 'Use a bounded retained-program collection');
  validateProgramCriterion(value.criterion);
  need(Array.isArray(value.alphabet) && Array.isArray(value.pages), 'Retained collection inputs are missing');
  const runeNames = new Set(value.alphabet.map(entry => entry.rune));
  const runeCounts = value.pages.map(page => {
    need(typeof page.text === 'string', 'Retained collection page text is missing');
    return Array.from(page.text).filter(character => runeNames.has(character)).length;
  });
  const seen = new Set();
  for (const program of value.programs) {
    validateProgram(value, program, runeCounts);
    need(!seen.has(program.id), 'Retained collection program IDs must be unique');
    seen.add(program.id);
  }
  freeze(value);
  const handle = Object.freeze({});
  handles.set(handle, value);
  return handle;
}

export function inspect(handle) {
  const value = handles.get(handle);
  need(value, 'Use a private retained collection handle');
  return freeze({schema: SCHEMA, count: value.programs.length,
    programs: value.programs.map(program => ({id: program.id, createdAt: program.createdAt}))});
}

export async function hydrate(handle, programId, crypto = globalThis.crypto) {
  const value = handles.get(handle);
  need(value, 'Use a private retained collection handle');
  need(typeof programId === 'string', 'Select one exact retained program ID');
  const program = value.programs.find(item => item.id === programId);
  need(program, 'The selected retained program is absent');
  const retained = await prepareRetainedRuneOutputs({
    task: taskFor(value, program), outputs: program.outputs, createdAt: program.createdAt
  }, crypto);
  // Expected control results remain independently generated and checked by the
  // existing helper; a stored collection cannot authorize its own expectations.
  need(same(retained.controls, program.controls), 'Stored retained controls differ from the verified fixed program');
  return retained;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const flags = process.argv.slice(2);
  need(flags.length === 2 && flags[0] === '--check', 'Use --check retained-collection.json');
  need((await stat(flags[1])).size <= LIMITS.bytes, 'Retained collection file exceeds its byte bound');
  const bytes = await readFile(flags[1]);
  need(bytes.byteLength <= LIMITS.bytes, 'Retained collection file exceeds its byte bound');
  const value = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
  const handle = prepare(value), model = inspect(handle);
  for (const program of model.programs) await hydrate(handle, program.id);
  console.log('PASS ' + model.count + ' retained programs and their independent controls verified; no missing outputs generated');
}
