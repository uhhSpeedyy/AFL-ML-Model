// Differential tests execute the exported Python package in the actual WASM runtime.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { loadPyodide } from './dist/static/pyodide/pyodide.mjs';

const py = await loadPyodide();
const files = JSON.parse(readFileSync(new URL('./dist/static/book-python.json', import.meta.url)));
py.FS.mkdirTree('/home/pyodide/book_recommender');
for (const [path, content] of Object.entries(files)) py.FS.writeFile(`/home/pyodide/${path}`, content);
py.runPython('from browser_runtime import dispatch_json');
const dispatch = py.globals.get('dispatch_json');
const cases = JSON.parse(readFileSync(new URL('./.cache/parity-cases.json', import.meta.url)));
for (const item of cases) {
  const result = JSON.parse(dispatch(JSON.stringify(item.message)));
  assert.equal(result.status, item.expected.status, item.name);
  assert.deepEqual(result.body, item.expected.body, item.name);
}
const plan = JSON.parse(dispatch(JSON.stringify({ operation: 'search', query: 'Dune' })));
assert.equal(plan.search.q, 'Dune');
assert.equal(plan.search.limit, 16);
dispatch.destroy();
console.log(`${cases.length} browser-runtime parity cases passed; async search planning passed.`);
