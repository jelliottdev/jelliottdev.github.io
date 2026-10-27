/* Preserve an already computed fixed result; never invent or fill missing output. */
import {createHash} from 'node:crypto';
import {readFile, writeFile, stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import E from '../local-experiment.js';
import Controls from '../local-plan-controls.js';
import J from '../finite-json.js';
import {validateProgramCriterion} from '../services/idea-assistant/published-program-source-index.mjs';

export const SCHEMA = 'liberpedia-retained-program-output-v1';
const MAX_BYTES = 8 * 1024 * 1024;
const copy = value => J.capture(value, {maxBytes: MAX_BYTES, maxDepth: 24, maxNodes: 500000});
const same = (a, b) => E.stable(a) === E.stable(b);
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const need = (value, message) => { if (!value) throw Error(message); };
const sha = value => createHash('sha256').update(E.stable(value)).digest('hex');
const date = value => typeof value === 'string'
  && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value)
  && Number.isFinite(Date.parse(value)) && new Date(value).toISOString() === value;

export async function validateRetainedProgramOutput(input, crypto = globalThis.crypto) {
  const value = copy(input);
  const unchanged = () => need(same(copy(input), value), 'Retained program output changed during verification');
  need(exact(value, ['schema', 'inputVersion', 'task', 'run', 'controls']) && value.schema === SCHEMA
    && value.inputVersion === 'raw' && exact(value.run, ['id', 'createdAt', 'result'])
    && date(value.run.createdAt), 'Use an exact retained raw program output');
  validateProgramCriterion(value.task.criterion);
  await E.checkIdentity(value.task, crypto);
  unchanged();
  need(value.run.id === sha(value.run.result), 'The retained result identity changed');
  await E.verify(value.task, value.run.result, crypto);
  unchanged();
  await Controls.validate(value.controls, value.task, crypto);
  unchanged();
  return value;
}

export async function prepareRetainedProgramOutput(input, crypto = globalThis.crypto) {
  const value = copy(input);
  const unchanged = () => need(same(copy(input), value), 'The supplied retained calculation changed');
  need(exact(value, ['task', 'result', 'createdAt']) && date(value.createdAt),
    'Supply an existing task, complete result and exact date');
  validateProgramCriterion(value.task.criterion);
  await E.checkIdentity(value.task, crypto);
  unchanged();
  await E.verify(value.task, value.result, crypto);
  unchanged();
  const controls = await Controls.prepare(value.task, crypto);
  unchanged();
  await Controls.validate(controls, value.task, crypto);
  unchanged();
  return {
    schema: SCHEMA, inputVersion: 'raw', task: value.task,
    run: {id: sha(value.result), createdAt: value.createdAt, result: value.result}, controls
  };
}

function resultFromCompleteVectors(task, outputs) {
  E.validateTask(task);
  validateProgramCriterion(task.criterion);
  need(Array.isArray(outputs) && outputs.length === task.pages.length,
    'Supply one complete saved output vector for every task page');
  const runeIndex = new Map(task.alphabet.map((entry, index) => [entry.rune, index]));
  const counts = Array(29).fill(0), transformed = [], matches = [];
  let runes = 0, adjacentPairs = 0, equalAdjacentPairs = 0;
  for (let index = 0; index < task.pages.length; index++) {
    const page = task.pages[index], output = outputs[index];
    need(exact(output, ['page', 'values']) && output.page === page.id && Array.isArray(output.values)
      && output.values.every(value => Number.isInteger(value) && value >= 0 && value < 29),
    'Saved output vectors must have the exact page order and rune indices');
    const characters = Array.from(page.text), values = output.values;
    need(values.length === characters.filter(character => runeIndex.has(character)).length,
      'A saved output vector is incomplete or longer than its full page');
    let at = 0;
    const text = characters.map(character => runeIndex.has(character)
      ? task.alphabet[values[at++]].rune : character).join('');
    transformed.push({page: page.id, text});
    for (let position = 0; position < values.length; position++) {
      counts[values[position]]++;
      if (position > 0 && values[position] === values[position - 1]) equalAdjacentPairs++;
    }
    runes += values.length;
    adjacentPairs += Math.max(0, values.length - 1);
    if (task.criterion.kind === 'exact-prefix') {
      matches.push({page: page.id,
        matched: task.criterion.values.every((value, position) => values[position] === value)});
    } else {
      const matchingOpenings = task.criterion.openings.filter(opening => opening.values
        .every((value, position) => values[position] === value)).map(opening => opening.id);
      matches.push({page: page.id, matched: matchingOpenings.length > 0, matchingOpenings});
    }
  }
  return {
    schema: E.RESULT, taskId: task.taskId, engine: E.ENGINE, runnerVersion: '1',
    metrics: {pages: task.pages.length, runes, adjacentPairs, equalAdjacentPairs,
      ioc: runes > 1 ? counts.reduce((total, count) => total + count * (count - 1), 0)
        / (runes * (runes - 1)) : 0}, matches, transformed
  };
}

export async function prepareRetainedRuneOutputs(input, crypto = globalThis.crypto) {
  const value = copy(input);
  const unchanged = () => need(same(copy(input), value), 'The saved rune-vector input changed during verification');
  need(exact(value, ['task', 'outputs', 'createdAt']) && date(value.createdAt),
    'Supply the exact task, saved page vectors and retained calculation date');
  // This constructs the result from the supplied archived values. It never asks
  // the decoder to generate a missing, short, reordered or incorrect vector.
  const result = resultFromCompleteVectors(value.task, value.outputs);
  const retained = await prepareRetainedProgramOutput({task: value.task, result, createdAt: value.createdAt}, crypto);
  unchanged();
  return retained;
}

async function readBoundedJSON(path) {
  need((await stat(path)).size <= MAX_BYTES, 'Retained input file exceeds its byte bound');
  const bytes = await readFile(path);
  need(bytes.length <= MAX_BYTES, 'Retained input file exceeds its byte bound');
  return JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const flags = process.argv.slice(2);
  if (flags.length === 2 && flags[0] === '--check') {
    await validateRetainedProgramOutput(await readBoundedJSON(flags[1]));
    console.log('PASS retained calculation and independent controls verified; no missing output generated');
  } else {
    need(flags.length === 4 && flags[0] === '--from-vectors' && flags[2] === '--out'
      && flags[1] && flags[3], 'Use --check file or --from-vectors input --out new-file');
    const retained = await prepareRetainedRuneOutputs(await readBoundedJSON(flags[1]));
    const text = E.stable(retained) + '\n';
    need(Buffer.byteLength(text) <= MAX_BYTES, 'Retained output file exceeds its byte bound');
    await writeFile(flags[3], text, {flag: 'wx'});
    console.log('PASS new retained file written exclusively from complete saved rune vectors');
  }
}
