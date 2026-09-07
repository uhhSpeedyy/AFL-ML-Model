"""Shared presentation adapters for Flask and the browser runtime."""

from urllib.parse import quote_plus


def _book_length_label(pages: object) -> str | None:
    try:
        count = int(float(pages))
    except (TypeError, ValueError, OverflowError):
        return None
    if count < 250:
        return "Short"
    if count < 400:
        return "Medium"
    if count < 600:
        return "Long"
    return "Epic"


def _book_for_browser(book: dict) -> dict:
    authors = [str(value) for value in book.get("author_name", []) if value]
    key = str(book.get("key") or "")
    if key.startswith("/works/"):
        open_library_url = f"https://openlibrary.org{key}"
    else:
        search_text = " ".join(
            value for value in [str(book.get("title") or ""), authors[0] if authors else ""] if value
        )
        open_library_url = f"https://openlibrary.org/search?q={quote_plus(search_text)}"
    return {
        **book,
        "authors": authors,
        "author": ", ".join(authors) or "Unknown author",
        "year": book.get("first_publish_year"),
        "open_library_url": open_library_url,
        "length_label": book.get("length_band")
        or _book_length_label(book.get("number_of_pages_median")),
        "themes": list(book.get("matched_themes") or []),
    }


def _recommendations_for_browser(payload: dict) -> dict:
    profile = payload.get("taste_profile", {})
    themes = [item.get("name") for item in profile.get("themes", []) if item.get("name")]
    styles = [
        item.get("name")
        for item in profile.get("style_proxies", [])
        if item.get("name")
    ]
    if themes:
        theme_phrase = " and ".join(themes[:2])
        summary = f"Themes: {theme_phrase}."
    else:
        summary = "Mixed themes."
    if styles:
        summary += f" Style: {styles[0]}."

    lists = []
    for index, shortlist in enumerate(payload.get("shortlists", [])):
        basis = shortlist.get("basis")
        if isinstance(basis, dict):
            titles = [str(value) for value in basis.get("favourite_titles", []) if value]
            description = (
                f"Based on {', '.join(titles[:3])}."
                if titles
                else "Matches one of your main themes."
            )
        else:
            description = "Closest overall matches." if index == 0 else str(
                basis or "Matches your selected books."
            )
        lists.append(
            {
                "id": f"shortlist-{index + 1}",
                "title": shortlist.get("name", "Reading direction"),
                "description": description,
                "books": [_book_for_browser(book) for book in shortlist.get("books", [])],
            }
        )

    return {
        "profile": {
            "themes": themes,
            "styles": styles,
            "summary": summary,
            "details": profile,
        },
        "lists": lists,
        "meta": {
            **payload.get("model", {}),
            "notices": payload.get("notices", []),
        },
    }
