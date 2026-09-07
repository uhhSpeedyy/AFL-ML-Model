"""Export only public site assets. No Azure, SQL, model binary or raw AFL data."""
from __future__ import annotations

import ast
import base64
import hashlib
import io
import json
import shutil
import sys
import tarfile
from dataclasses import replace
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DIST = ROOT / "cloudflare" / "dist"
VERSION = "314.0.6"
INTEGRITY = "BKDTJyIqFxC4BExLqeRS3f5xvXZIjOt8C3zGLN/Cc7tFxSwvKVhVkchQQ2AGLOtR4YrVOIFxbV8poyDOOmWwxQ=="


def browser_sources():
    # Keep the pure language/edition helpers from the original HTTP client.
    source = (APP / "book_recommender/open_library.py").read_text()
    tree = ast.parse(source)
    names = {"SEARCH_FIELDS", "LANGUAGE_PARAMS", "_language_param", "_edition_documents", "_language_ranked_document", "OpenLibraryUnavailable"}
    selected = [n for n in tree.body if getattr(n, "name", None) in names or (
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets))]
    helpers = "from __future__ import annotations\nfrom typing import Any\n\n"
    helpers += "\n\n".join(ast.get_source_segment(source, n) for n in selected)
    helpers += '\n\nclass OpenLibraryClient:\n    def __init__(self):\n        raise RuntimeError("A browser client must be supplied")\n'
    files = {"book_recommender/__init__.py": "", "book_recommender/open_library.py": helpers}
    for name in ("service.py", "catalogue.py", "browser.py"):
        files[f"book_recommender/{name}"] = (APP / "book_recommender" / name).read_text()
    files["browser_runtime.py"] = (ROOT / "cloudflare/browser_runtime.py").read_text()
    return files


def vendor_runtime():
    archive = ROOT / "cloudflare" / ".cache" / f"pyodide-{VERSION}.tgz"
    if not archive.exists():
        response = requests.get(f"https://registry.npmjs.org/pyodide/-/pyodide-{VERSION}.tgz", timeout=90)
        response.raise_for_status()
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(response.content)
    data = archive.read_bytes()
    if base64.b64encode(hashlib.sha512(data).digest()).decode() != INTEGRITY:
        raise RuntimeError("Pyodide package integrity check failed")
    dest = DIST / "static/pyodide"
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            path = Path(member.name)
            if member.isfile() and path.parent == Path("package") and (
                path.suffix in {".js", ".mjs", ".wasm", ".zip", ".json"} or path.name.startswith("LICENSE")
            ):
                (dest / path.name).write_bytes(tar.extractfile(member).read())
    shutil.copyfile(ROOT / "cloudflare/PYODIDE-LICENSE.txt", dest / "LICENSE.txt")


def build():
    sys.path.insert(0, str(APP))
    from app import create_app
    from afl_ml.settings import Settings

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    settings = replace(Settings(), database_enabled=False, database_read_enabled=False, db_server=None)
    client = create_app(settings).test_client()
    for route, output in {"/": "index.html", "/afl": "afl.html", "/books": "books.html",
                          "/api/predictions": "api/predictions.json", "/api/model": "api/model.json",
                          "/api/books/model": "api/books/model.json", "/health": "health.json", "/ready": "ready.json"}.items():
        response = client.get(route)
        assert response.status_code == 200, route
        dest = DIST / output
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = response.get_data(as_text=True)
        if route == "/books":
            text = text.replace('src="/static/books.js" defer', 'src="/static/books.js" type="module"')
            text = text.replace('<body>', '<body>\n<noscript>This book recommender needs JavaScript enabled.</noscript>')
            text = text.replace('<p class="search-status"', '<p class="runtime-note">The book model loads on your first search. Your saved favourites stay in this browser.</p>\n<p class="search-status"', 1)
        if route == "/afl":
            text = text.replace('Home, away and draw probabilities add to 100%.', 'Probabilities are for regulation time; a draw in finals leads to extra time.')
        dest.write_text(text)
    shutil.copytree(APP / "static", DIST / "static")
    js = DIST / "static/books.js"
    js.write_text('import { bookFetch } from "./book-client.js";\n' + js.read_text().replace('await fetch(', 'await bookFetch('))
    for name in ("book-client.js", "book-worker.js"):
        shutil.copyfile(ROOT / "cloudflare" / name, DIST / "static" / name)
    (DIST / "static/book-python.json").write_text(json.dumps(browser_sources()))
    (DIST / "404.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Page not found</title><h1>Page not found</h1><p><a href="/">Return home</a></p></html>')
    (DIST / "_redirects").write_text('/api/predictions /api/predictions.json 200\n/api/model /api/model.json 200\n/api/books/model /api/books/model.json 200\n/health /health.json 200\n/ready /ready.json 200\n')
    (DIST / "_headers").write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/static/pyodide/*\n  Cache-Control: public, max-age=86400\n/api/*\n  Cache-Control: public, max-age=60\n')
    vendor_runtime()
    paths = [p for p in DIST.rglob('*') if p.is_file()]
    assert all(p.stat().st_size < 25 * 1024 * 1024 for p in paths)
    print(f"Exported {len(paths)} public files ({sum(p.stat().st_size for p in paths)/1024/1024:.1f} MiB)")


if __name__ == "__main__":
    build()
