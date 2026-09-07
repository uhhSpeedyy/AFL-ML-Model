// Preserve the existing UI's response contract while computing in a Web Worker.
let worker;
let sequence = 0;
const pending = new Map();

export function bookFetch(path, options = {}) {
  if (options.signal?.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'));
  if (!worker) {
    worker = new Worker('/static/book-worker.js', { type: 'module' });
    worker.onmessage = ({ data }) => pending.get(data.id)?.resolve(
      new Response(JSON.stringify(data.body), { status: data.status, headers: { 'Content-Type': 'application/json' } }),
    );
    worker.onerror = () => {
      for (const task of [...pending.values()]) task.reject(new Error('Book model failed to load'));
      worker.terminate();
      worker = null;
    };
  }
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    const cleanup = () => { pending.delete(id); options.signal?.removeEventListener('abort', abort); clearTimeout(timer); };
    const abort = () => { worker?.postMessage({ id, cancel: true }); cleanup(); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => {
      worker?.postMessage({ id, cancel: true }); cleanup();
      reject(new Error('Loading the book model took too long. Please try again.'));
    }, 90000);
    pending.set(id, {
      resolve: response => { cleanup(); resolve(response); },
      reject: error => { cleanup(); reject(error); },
    });
    options.signal?.addEventListener('abort', abort, { once: true });
    const url = new URL(path, location.origin);
    worker.postMessage({ id,
      operation: url.pathname.endsWith('/search') ? 'search' : 'recommend',
      query: url.searchParams.get('q'),
      body: options.body ? JSON.parse(options.body) : undefined,
    });
  });
}
