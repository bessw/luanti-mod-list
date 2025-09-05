"""
ContentDB API functions
This module provides access to the Luanti Content Database (ContentDB) from Lanti.
api: https://content.luanti.org/help/api/
"""
import requests
from db_utils import save_result, contentdb_url_exists

def search_contentdb_mods(query, page=1, per_page=10):
    url = "https://content.luanti.org/api/packages/"
    params = {
        "type": "mod",
        "q": query,
        "page": page,
        "num": per_page
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    response_data = resp.json()
    # Handle both paginated and direct array responses
    if isinstance(response_data, dict) and "items" in response_data:
        items = response_data.get("items", [])
    elif isinstance(response_data, list):
        items = response_data
    else:
        items = []
    results = []
    for item in items:
        author = item.get("author", "")
        name = item.get("name", "")
        contentdb_url = item.get("url", f"https://content.luanti.org/packages/{author}/{name}/")
        if contentdb_url_exists(contentdb_url):
            continue
        details_url = f"https://content.luanti.org/api/packages/{author}/{name}/"
        details_resp = requests.get(details_url)
        details_resp.raise_for_status()
        details = details_resp.json()
        result = {
            "contentdb_url": details.get("url", contentdb_url),
            "forum_url": details.get("forum_url", details.get("forums", "")),
            "repo_url": details.get("repo", details.get("repo_url", "")),
            "name": details.get("name", ""),
            "short_description": details.get("short_description", ""),
            "dev_state": details.get("dev_state", ""),
            "tags": details.get("tags", []),
            "content_warnings": details.get("content_warnings", []),
            "license": details.get("license", ""),
            "media_license": details.get("media_license", ""),
            "long_description": details.get("long_description", ""),
            "website": details.get("website", ""),
            "issue_tracker": details.get("issue_tracker", ""),
            "video_url": details.get("video_url", ""),
            "donate_url": details.get("donate_url", ""),
            "translation_url": details.get("translation_url", ""),
            "type": details.get("type", item.get("type", "mod")),
            "title": details.get("title", item.get("title", item.get("name", ""))),
            "author": details.get("author", item.get("author", "")),
            "description": details.get("description", item.get("description", ""))
        }
        save_result(result, "contentdb")
        results.append(result)
    return results
