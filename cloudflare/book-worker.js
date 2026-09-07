import { loadPyodide } from './pyodide/pyodide.mjs';

let runtime;
let queue = Promise.resolve();
let lastRequest = 0;
const tasks = new Map();
const cache = new Map();

async function initialise() {
  const py = await loadPyodide({ indexURL: new URL('./pyodide/', import.meta.url).href });
  const response = await fetch('/static/book-python.json');
  if (!response.ok) throw new Error('The book model could not be loaded. Please reload and try again.');
  const files = await response.json();
  py.FS.mkdirTree('/home/pyodide/book_recommender');
  for (const [path, content] of Object.entries(files)) {
    py.FS.writeFile(`/home/pyodide/${path}`, content);
  }
  py.runPython('from browser_runtime import dispatch_json');
  return py;
}

async function searchLibrary(search, signal) {
  const url = new URL('https://openlibrary.org/search.json');
  for (const name of ['q', 'limit', 'lang', 'fields']) url.searchParams.set(name, search[name]);
  const key = url.href;
  const saved = cache.get(key);
  if (saved && Date.now() - saved.at < 600000) return saved.value;
  try {
    const wait = Math.max(0, 1100 - (Date.now() - lastRequest));
    if (wait) await new Promise(resolve => setTimeout(resolve, wait));
    signal.throwIfAborted();
    lastRequest = Date.now();
    const response = await fetch(url, {
      signal: AbortSignal.any([signal, AbortSignal.timeout(12000)]),
      credentials: 'omit', referrerPolicy: 'no-referrer',
    });
    if (!response.ok) throw new Error('Search unavailable');
    const payload = await response.json();
    if (!Array.isArray(payload.docs)) throw new Error('Invalid search response');
    const value = { docs: payload.docs.slice(0, search.limit) };
    if (cache.size >= 50) cache.delete(cache.keys().next().value);
    cache.set(key, { at: Date.now(), value });
    return value;
  } catch (error) {
    if (signal.aborted) throw error;
    return { failed: true };
  }
}

async function run(message, controller) {
  try {
    if (controller.signal.aborted) return;
    runtime ||= initialise().catch(error => { runtime = null; throw error; });
    const py = await runtime;
    controller.signal.throwIfAborted();
    const dispatch = py.globals.get('dispatch_json');
    let result;
    try {
      result = JSON.parse(dispatch(JSON.stringify(message)));
      if (result.search) {
        message.remote = await searchLibrary(result.search, controller.signal);
        result = JSON.parse(dispatch(JSON.stringify(message)));
      }
    } finally {
      dispatch.destroy();
    }
    if (!controller.signal.aborted) self.postMessage({ id: message.id, ...result });
  } catch (error) {
    if (!controller.signal.aborted) self.postMessage({
      id: message.id, status: 503,
      body: { error: 'The book model could not start. Please reload the page and try again.' },
    });
  } finally {
    tasks.delete(message.id);
  }
}

self.onmessage = ({ data }) => {
  if (data.cancel) { tasks.get(data.id)?.abort(); return; }
  const controller = new AbortController();
  tasks.set(data.id, controller);
  queue = queue.then(() => run(data, controller));
};
