# ============================================================
# File: blog_src/scripts/writer/google_cse.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\google_cse.py
# ============================================================
from __future__ import annotations

import json
import os
import re
from typing import List, Dict, Optional, Any

try:
    import requests
except Exception:
    requests = None

try:
    from dotenv import load_dotenv  # optional
except Exception:
    load_dotenv = None

API_URL = "https://www.googleapis.com/customsearch/v1"

BLOCK_DOMAINS = [
    "amazon.", "ebay.", "walmart.", "pinterest.", "reddit.", "aliexpress.", "facebook.", "instagram.",
    "/tag/", "/category/"
]


def _load_env() -> None:
    if load_dotenv:
        try:
            load_dotenv()
        except Exception:
            pass


def _http_get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if requests is None:
        from urllib.parse import urlencode
        from urllib.request import urlopen
        full = f"{url}?{urlencode(params)}"
        with urlopen(full) as resp:
            return json.loads(resp.read().decode("utf-8"))
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _looks_blocked(url: str) -> bool:
    u = url.lower()
    return any(b in u for b in BLOCK_DOMAINS)


def fetch_sources(seed: str, longtail: str, n: int = 5,
                  gl: str = "us", lr: str = "lang_en",
                  api_key: Optional[str] = None, cse_id: Optional[str] = None) -> List[Dict[str, str]]:
    _load_env()
    api_key = api_key or os.getenv("GOOGLE_API_KEY", "").strip()
    cse_id  = cse_id  or os.getenv("GOOGLE_CSE_ID", "").strip()
    if not api_key or not cse_id:
        raise RuntimeError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set in environment.")

    query = f"{seed} {longtail}".strip()
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": max(1, min(int(n * 2), 10)),
        "gl": gl,
        "lr": lr,
        "safe": "off",
    }
    data = _http_get(API_URL, params)

    items = data.get("items", []) if isinstance(data, dict) else []
    results: List[Dict[str, str]] = []
    for it in items:
        link = it.get("link", "")
        title = (it.get("title") or "").strip()
        snippet = (it.get("snippet") or "").strip()
        if not link or not title or not snippet:
            continue
        if _looks_blocked(link):
            continue
        snippet = re.sub(r"\s+", " ", snippet).strip()
        results.append({"title": title, "url": link, "snippet": snippet})
        if len(results) >= n:
            break

    return results


def build_sources_summary(sources: List[Dict[str, str]], max_chars: int = 1200) -> str:
    chunks = []
    for i, s in enumerate(sources, 1):
        chunks.append(f"[{i}] {s['title']} — {s['snippet']} (Source: {s['url']})")
    text = "\n".join(chunks)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"
    return text
