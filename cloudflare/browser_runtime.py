"""Run the original recommender with asynchronously supplied Open Library data.

The JS worker calls once to discover the search, fetches it, then replays with
that response. The model remains synchronous and identical to local Python.
"""
import json
from book_recommender.service import BookRecommendationService
from book_recommender.open_library import (
    OpenLibraryUnavailable, SEARCH_FIELDS, _language_param, _language_ranked_document,
)
from book_recommender.browser import _book_for_browser, _recommendations_for_browser


class NeedSearch(Exception):
    def __init__(self, query, limit, language):
        self.request = {
            "q": query, "limit": limit, "language": language,
            "lang": _language_param(language) or "en", "fields": ",".join(SEARCH_FIELDS),
        }


class BrowserClient:
    response = None

    def search(self, query, *, limit=8, language="eng"):
        if self.response is None:
            raise NeedSearch(query, limit, language)
        if self.response.get("failed"):
            raise OpenLibraryUnavailable("Open Library is temporarily unavailable")
        return [_language_ranked_document(doc, language)
                for doc in self.response.get("docs", [])[:limit] if isinstance(doc, dict)]


client = BrowserClient()
service = BookRecommendationService(client=client)


def dispatch(message):
    client.response = message.get("remote")
    try:
        if message["operation"] == "search":
            query = " ".join(str(message.get("query", "")).split())
            if not 2 <= len(query) <= 120:
                raise ValueError("Enter between 2 and 120 characters to search for a book.")
            result = service.search(query, limit=8)
            books = [_book_for_browser(book) for book in result["results"]]
            if result.get("degraded") and not books:
                return {"status": 503, "body": {"error": "Book search is temporarily unavailable. Please try again."}}
            body = {"books": books, "source": result["source"], "degraded": result["degraded"]}
        elif message["operation"] == "recommend":
            body = message.get("body")
            if not isinstance(body, dict):
                raise ValueError("Send a JSON object with a favourites list.")
            favourites = body.get("favourites")
            if not isinstance(favourites, list) or not 1 <= len(favourites) <= 10:
                raise ValueError("Choose between one and ten favourite books.")
            preferences = body.get("preferences")
            if preferences is None:
                preferences = {}
            if not isinstance(preferences, dict):
                raise ValueError("Preferences must be a JSON object.")
            discovery = preferences.get("discovery")
            options = {
                "shortlist_size": 6, "theme_list_count": 3,
                "allow_same_author": discovery != "adventurous",
                "author_emphasis": 2.0 if discovery == "familiar" else 1.0,
                "ignore_length": preferences.get("length") == "any",
            }
            if preferences.get("era") == "modern":
                options["preferred_era"] = ["Modern", "Contemporary"]
            elif preferences.get("era") == "classics":
                options["preferred_era"] = ["Classic", "Post-war"]
            body = _recommendations_for_browser(service.recommend(favourites, options))
            if client.response and client.response.get("failed"):
                body["meta"]["notices"].append("Open Library is unavailable; these suggestions use the backup catalogue.")
        else:
            return {"status": 404, "body": {"error": "Unknown operation"}}
        return {"status": 200, "body": body}
    except NeedSearch as search:
        return {"search": search.request}
    except ValueError as error:
        return {"status": 400, "body": {"error": str(error)}}


def dispatch_json(message):
    return json.dumps(dispatch(json.loads(message)))
