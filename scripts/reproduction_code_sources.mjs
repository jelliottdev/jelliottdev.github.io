/* Read exact retained implementation bytes. No code loading or source execution. */
import {readFile, stat, realpath} from 'node:fs/promises';
import {resolve, relative, isAbsolute, extname, dirname} from 'node:path';
import {createHash} from 'node:crypto';
import J from '../finite-json.js';

const POLICY = 'data/maintained-reproduction-code-policy.json';
const MANIFEST = 'data/reproduction-code-archive.json';
const MAX_SOURCE = 2 * 1024 * 1024, MAX_TOTAL = 32 * 1024 * 1024;
const need = (value, message) => { if (!value) throw Error(message); };
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const hex = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const maintained = value => typeof value === 'string' && value.length <= 300
  && /^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_.-]+)*\.(?:js|mjs)$/.test(value)
  && value.split('/').every(part => part && part !== '.' && part !== '..')
  && (!value.includes('/') || value.startsWith('scripts/') || value.startsWith('services/'));

async function bounded(root, name) {
  need(typeof name === 'string' && name.length <= 500 && /^[A-Za-z0-9_./-]+$/.test(name)
    && name.split('/').every(part => part && part !== '.' && part !== '..'), 'Unsafe maintained code path');
  const target = await realpath(resolve(root, name)), child = relative(root, target);
  need(child && !child.startsWith('..') && !isAbsolute(child), 'Maintained code path escapes repository');
  need((await stat(target)).size <= MAX_SOURCE, 'Maintained code exceeds its byte bound');
  const bytes = await readFile(target);
  need(bytes.length > 0 && bytes.length <= MAX_SOURCE, 'Maintained code exceeds its byte bound');
  return bytes;
}

function parse(bytes) {
  const text = new TextDecoder('utf-8', {fatal: true}).decode(bytes), value = JSON.parse(text);
  // Each shadowed JSON property discards at least its key string. Comparing
  // lexical string counts also catches escaped duplicate names at any depth.
  const strings = text => (text.match(/"(?:[^"\\]|\\.)*"/g) || []).length;
  need(strings(text) === strings(JSON.stringify(value)), 'Repeated JSON field');
  return J.capture(value, {maxBytes: MAX_SOURCE, maxDepth: 8, maxNodes: 10000});
}

export async function readRetainedCode(root, pin) {
  pin = J.capture(pin, {maxBytes: 1024, maxDepth: 2, maxNodes: 5});
  need(exact(pin, ['path', 'sha256']) && maintained(pin.path) && hex(pin.sha256),
    'Use an exact maintained code pin');
  root = await realpath(resolve(root));
  let ancestor = resolve(root, pin.path);
  while (true) {
    try {
      const child = relative(root, await realpath(ancestor));
      need(!child.startsWith('..') && !isAbsolute(child), 'Maintained source path escapes repository');
      break;
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      const parent = dirname(ancestor);
      need(parent !== ancestor, 'Maintained source has no repository ancestor');
      ancestor = parent;
    }
  }
  const policy = parse(await bounded(root, POLICY));
  need(exact(policy, ['schema', 'paths'])
    && policy.schema === 'liberpedia-maintained-reproduction-code-policy-v1'
    && Array.isArray(policy.paths) && policy.paths.length >= 1 && policy.paths.length <= 32
    && policy.paths.every(maintained) && new Set(policy.paths).size === policy.paths.length,
  'Invalid maintained code policy');
  need(policy.paths.includes(pin.path), 'The reproduction source is not maintained code');
  const manifest = parse(await bounded(root, MANIFEST));
  need(exact(manifest, ['schema', 'entries']) && manifest.schema === 'liberpedia-reproduction-code-archive-v1'
    && Array.isArray(manifest.entries) && manifest.entries.length <= 512,
  'Invalid maintained code archive manifest');
  const associations = new Map(), objects = new Map();
  for (const item of manifest.entries) {
    need(exact(item, ['sourcePath', 'sha256', 'bytes', 'path']) && maintained(item.sourcePath)
      && policy.paths.includes(item.sourcePath) && hex(item.sha256)
      && Number.isSafeInteger(item.bytes) && item.bytes > 0 && item.bytes <= MAX_SOURCE
      && item.path === 'published-sources/code/' + item.sha256 + extname(item.sourcePath),
    'Invalid maintained code archive association');
    const key = item.sourcePath + '|' + item.sha256;
    need(!associations.has(key), 'Repeated maintained code archive association');
    associations.set(key, item);
    need(!objects.has(item.path) || objects.get(item.path) === item.bytes, 'Conflicting retained code object size');
    objects.set(item.path, item.bytes);
  }
  need([...objects.values()].reduce((sum, size) => sum + size, 0) <= MAX_TOTAL,
    'Maintained code archive exceeds its total byte bound');
  const item = associations.get(pin.path + '|' + pin.sha256);
  need(item, 'No exact retained maintained code version');
  const bytes = await bounded(root, item.path);
  need(bytes.length === item.bytes && sha(bytes) === pin.sha256, 'Retained maintained code bytes changed');
  return {bytes, sourcePath: item.path};
}
