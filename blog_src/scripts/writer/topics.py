# blog_src/scripts/writer/topics.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import json

DATA_DIR = Path("blog_src/data")
CATEGORIES_FILE = DATA_DIR / "categories.json"
STATE_FILE = DATA_DIR / "state.json"


def _norm(s):
    return (s or "").strip()


def _load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        return default


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_keywords_and_topics(categories_path: Path = CATEGORIES_FILE):
    """
    Load keywords from categories.json and return a tuple:
      (keywords, topics)
    where:
      - keywords: flat list[str]
      - topics: list[{"category": str, "slug": str, "keyword": str}]
    """
    if not categories_path.exists():
        return [], []

    try:
        with categories_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return [], []

    cats = data.get("categories", [])
    topics = []
    for cat in cats:
        name = _norm(cat.get("name"))
        slug = _norm(cat.get("slug"))
        for kw in cat.get("keywords", []):
            kw_s = _norm(kw)
            if kw_s:
                topics.append({"category": name, "slug": slug, "keyword": kw_s})

    keywords = [t["keyword"] for t in topics]
    return keywords, topics


def keyword_to_category(keyword: str, topics: list[dict]) -> tuple[str | None, str]:
    """
    Given a keyword and topics list, return (category_name, slug) or (None, "").
    """
    k = (keyword or "").strip().lower()
    for t in topics or []:
        if (t.get("keyword", "").strip().lower() == k) and t.get("category"):
            return t.get("category"), t.get("slug") or ""
    return None, ""


# === NEW: Category-first rotation with failsafe ===
def get_next_keyword_and_category(
    categories_path: Path = CATEGORIES_FILE,
    state_path: Path = STATE_FILE,
) -> tuple[str, str | None, str]:
    """
    Returns (keyword, category_name, category_slug) using round-robin category rotation.
    State is persisted in state.json with:
      - last_category: int (index of the last used category)
      - kw_pos: { <category_slug>: last_used_keyword_index }
    If categories.json is missing or empty, returns ("", None, "").
    """

    data = _load_json(categories_path, {"categories": []})
    cats = data.get("categories", []) or []
    cat_list = []
    for c in cats:
        name = _norm(c.get("name"))
        slug = _norm(c.get("slug"))
        kws = [_norm(k) for k in (c.get("keywords") or []) if _norm(k)]
        if name and kws:
            cat_list.append({"name": name, "slug": slug, "keywords": kws})

    if not cat_list:
        return "", None, ""

    state = _load_json(state_path, {})

    # --- failsafe for invalid types ---
    try:
        last_cat = int(state.get("last_category", -1))
    except (TypeError, ValueError):
        last_cat = -1

    kw_pos = state.get("kw_pos") or {}
    if not isinstance(kw_pos, dict):
        kw_pos = {}

    # Select next category
    next_cat_idx = (last_cat + 1) % len(cat_list)
    cat = cat_list[next_cat_idx]
    slug = cat.get("slug") or f"cat-{next_cat_idx}"

    # Select next keyword inside this category
    last_kw_idx = int(kw_pos.get(slug, -1)) if str(kw_pos.get(slug, -1)).isdigit() else -1
    next_kw_idx = (last_kw_idx + 1) % len(cat["keywords"])
    keyword = cat["keywords"][next_kw_idx]

    # Persist state
    state["last_category"] = next_cat_idx
    kw_pos[slug] = next_kw_idx
    state["kw_pos"] = kw_pos
    _save_json(state_path, state)

    return keyword, cat["name"], slug
