/* Extract three exact saved row-route vectors; never run the historical search. */
import {readFile, writeFile, stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import E from '../../../local-experiment.js';
import {prepareSavedPrograms} from '../../../scripts/retain_saved_programs.mjs';

const ROOT = new URL('../../../', import.meta.url);
const BASE = 'experiments/records/lp2-row-column-routes/';
const OUTPUT = BASE + 'retained-row-programs.json';
// Explicit retained-output import date, not the historical experiment date.
const CREATED_AT = '2026-10-27T03:46:53.000Z';
const FROZEN = {
  'plan.json': '6aa1c4b82e176e47a94dd0fd344166a664001336bb2765a879eff9397d69ae3b',
  'results.json': '819dfe8eac592d9f10bede0675aae11020a14a3f962cdeb74e90ce13a0ce8d50',
  'run.py': '7db305eae184041f3bd4732625f7f240aa1da82170a722e94b6d72dae87c421c',
  'check.py': '946c001ee759be2e37e243e3407dbb427fc4d36cd4d444a61038222b4355811b'
};
const ROUTES = [
  {id: 'rows-original-order', title: 'Keep the original rune order and check nine passage openings',
    outer: false, inner: false, steps: []},
  {id: 'rows-reverse-within-line', title: 'Reverse the runes within every source line and check nine passage openings',
    outer: false, inner: true, steps: [{op: 'reverse', unit: 'line'}]},
  {id: 'rows-reverse-whole-page', title: 'Reverse all runes on each page and check nine passage openings',
    outer: true, inner: true, steps: [{op: 'reverse', unit: 'page'}]}
];
const need = (value, message) => { if (!value) throw Error(message); };
const same = (a, b) => E.stable(a) === E.stable(b);
const sha = value => createHash('sha256').update(value).digest('hex');
const read = async path => {
  const url = new URL(path, ROOT);
  need((await stat(url)).size <= 8 * 1024 * 1024, 'Row-route source exceeds its byte bound');
  const raw = await readFile(url);
  need(raw.length <= 8 * 1024 * 1024, 'Row-route source exceeds its byte bound');
  return raw;
};

export async function retainedPrograms() {
  const frozen = {};
  for (const [name, expected] of Object.entries(FROZEN)) {
    const raw = await read(BASE + name);
    need(sha(raw) === expected, 'Frozen row-route source changed: ' + name);
    if (name.endsWith('.json')) frozen[name] = JSON.parse(raw);
  }
  const plan = frozen['plan.json'], report = frozen['results.json'];
  need(report.schema === 'liberpedia-row-column-routes-v1'
    && report.plan_sha256 === FROZEN['plan.json'] && report.case_count === 880
    && report.matching_case_count === 0 && report.pages.length === 56
    && same(report.pages.map(page => page.page), plan.pages), 'Archived route inventory changed');
  const official = JSON.parse(await read('data/local-run-inputs.json'));
  need(same(report.alphabet, official.alphabet.map(row => row.rune)), 'Official row-route alphabet changed');
  const pages = [], eligible = [];
  for (const archived of report.pages) {
    const raw = await read('text/' + archived.page + '.txt');
    need(sha(raw) === archived.source_sha256, 'Archived row-route input changed');
    const text = raw.toString('utf8');
    need(official.pages.find(page => page.id === archived.page)?.raw === text, 'Official row-route text changed');
    if (!archived.source_positions.length) {
      need(archived.page === 'lp2-50' && archived.cases.length === 0,
        'Only the archived no-case empty page can be omitted');
      continue;
    }
    need(archived.cases.length === 16, 'A historical page lost a declared route');
    pages.push({id: archived.page, text});
    eligible.push(archived);
  }
  need(pages.length === 55, 'The saved rune-bearing page scope changed');
  for (const opening of plan.openings) need(sha(await read(opening.source)) === opening.sha256,
    'A historical opening source changed');
  const criterion = {kind: 'exact-prefix-set', openings: plan.openings.map(opening => ({id: opening.id, values: opening.indices}))};
  const programs = ROUTES.map(route => ({id: route.id, title: route.title, steps: route.steps, createdAt: CREATED_AT,
    outputs: eligible.map(page => {
      const cases = page.cases.filter(item => item.axis === 'row' && item.outer_reverse === route.outer
        && item.inner_reverse === route.inner && item.alternating === false);
      need(cases.length === 1, 'A selected historical route is missing or duplicated');
      const selected = cases[0], positions = page.source_positions;
      let expected;
      if (route.outer) expected = positions.map((_, index) => index).reverse();
      else if (!route.inner) expected = positions.map((_, index) => index);
      else {
        const lines = new Map();
        positions.forEach((position, index) => {
          if (!lines.has(position.line)) lines.set(position.line, []);
          lines.get(position.line).push(index);
        });
        expected = [...lines.values()].flatMap(line => line.toReversed());
      }
      need(same(selected.source_ordinals, expected), 'The selected saved source permutation changed');
      need(same(selected.output_indices, selected.source_ordinals.map(index => positions[index].index)),
        'The selected saved vector differs from its archived source trace');
      return {page: page.page, values: selected.output_indices};
    })}));
  return prepareSavedPrograms({alphabet: official.alphabet, pages, criterion, programs});
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const flags = process.argv.slice(2);
  need(flags.length === 1 && ['--check', '--write'].includes(flags[0]), 'Use --check or --write');
  const run = E.run;
  let syntheticRuns = 0;
  E.run = task => {
    need(task.title.startsWith('Synthetic local reference '), 'Only independent synthetic controls may be run');
    syntheticRuns++;
    return run(task);
  };
  try {
    const retained = await retainedPrograms(), raw = Buffer.from(E.stable(retained) + '\n');
    if (flags[0] === '--write') await writeFile(new URL(OUTPUT, ROOT), raw, {flag: 'wx'});
    else need((await read(OUTPUT)).equals(raw), 'Retained row-route output changed');
    console.log('PASS3 saved row routes ×55 pages;13 other routes remain outside this declaration;'
      + syntheticRuns + ' synthetic control runs, no historical search execution');
  } finally {
    E.run = run;
  }
}
