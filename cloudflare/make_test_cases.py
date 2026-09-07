"""Create reference responses from the original Flask routes for WASM tests."""
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from app import create_app
from afl_ml.settings import Settings
from book_recommender.service import BookRecommendationService
from book_recommender.catalogue import FALLBACK_CATALOGUE
from book_recommender.open_library import OpenLibraryUnavailable


class Client:
    def __init__(self, remote): self.remote = remote
    def search(self, *_args, **_kwargs):
        if self.remote.get("failed"): raise OpenLibraryUnavailable("unavailable")
        return self.remote.get("docs", [])


app = create_app(replace(Settings(), database_enabled=False, db_server=None))
cases = []
for index, preferences in enumerate([{}, {"discovery": "adventurous"}, {"discovery": "familiar"}, {"era": "modern"}, {"era": "classics", "length": "any"}]):
    remote = {"docs": list(FALLBACK_CATALOGUE)[10:25]}
    body = {"favourites": list(FALLBACK_CATALOGUE)[:3], "preferences": preferences}
    app.extensions['book_recommendation_service'] = BookRecommendationService(client=Client(remote))
    response = app.test_client().post('/api/books/recommend', json=body)
    cases.append({"name": f"recommendation preferences {index}", "message": {"operation": "recommend", "body": body, "remote": remote}, "expected": {"status": response.status_code, "body": response.json}})
for query, remote in [('Dune', {'docs': []}), ('Hobbit', {'failed': True}), ('zxydoesnotexist', {'failed': True})]:
    app.extensions['book_recommendation_service'] = BookRecommendationService(client=Client(remote))
    response = app.test_client().get('/api/books/search', query_string={'q': query})
    cases.append({"name": f"search {query}", "message": {"operation": "search", "query": query, "remote": remote}, "expected": {"status": response.status_code, "body": response.json}})
for body in [None, {}, {"favourites": []}, {"favourites": [{}]},
             {"favourites": list(FALLBACK_CATALOGUE)[:1], "preferences": []}]:
    response = app.test_client().post('/api/books/recommend', json=body)
    cases.append({"name": f"invalid request {body}", "message": {"operation": "recommend", "body": body, "remote": {"docs": []}}, "expected": {"status": response.status_code, "body": response.json}})
path = ROOT / 'cloudflare/.cache/parity-cases.json'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(cases))
