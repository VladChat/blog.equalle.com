# ============================================================
# File: blog_src/scripts/writer/rss_video_fetch.py
# ============================================================
"""
rss_video_fetch.py — YouTube smart video fetcher for eQualle blog

Назначение:
  - Подбирать подходящее видео под статью через YouTube Data API v3
  - Без участия LLM (переписка теперь выполняется внутри главного промпта)
  - Возвращать обогащённую структуру с title, description и link
  - Совместимо с main_local.py и prompt_builder

Зависимости:
  - google-api-python-client
  - python-dotenv
"""

from __future__ import annotations

import os
import re
import html
import json
from pathlib import Path
from typing import Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# ========== ENV & PATH ==========
_THIS_FILE = Path(__file__).resolve()
_BLOG_SRC_DIR = _THIS_FILE.parents[1]
if _BLOG_SRC_DIR.name != "blog_src":
    for p in _THIS_FILE.parents:
        if (p / "blog_src").is_dir():
            _BLOG_SRC_DIR = p / "blog_src"
            break

# Загружаем только онлайн .env (на уровень выше blog_src)
env_path = _THIS_FILE.parents[2] / ".env"
if load_dotenv(dotenv_path=env_path):
    print(f"[eQualle VideoFeed][INIT] ✅ .env loaded → {env_path}")
else:
    print("[eQualle VideoFeed][INIT] ⚠️ .env not found in online path.")

YT_API_KEY = os.getenv("YT_API_KEY")
if YT_API_KEY:
    print("[eQualle VideoFeed][INIT] 🔑 YT_API_KEY loaded successfully.")
else:
    print("[eQualle VideoFeed][INIT] ❌ YT_API_KEY is missing. Add it to your online .env file.")

_youtube_client = None

# ========== YOUTUBE CLIENT ==========
def _get_youtube():
    """Ленивое создание клиента YouTube API."""
    global _youtube_client
    if _youtube_client is None:
        if not YT_API_KEY:
            raise RuntimeError("YT_API_KEY missing — cannot initialize YouTube client.")
        try:
            print("[eQualle VideoFeed][INIT] 🚀 Initializing YouTube API client...")
            _youtube_client = build("youtube", "v3", developerKey=YT_API_KEY)
            print("[eQualle VideoFeed][INIT] ✅ YouTube API client ready.")
        except Exception as e:
            print(f"[eQualle VideoFeed][FATAL] ❌ Failed to init YouTube API client: {e}")
            raise
    return _youtube_client


# ========== HELPERS ==========
_SAFE_WORDS = re.compile(r"[a-z0-9\s\-\_\&\|\/]+", re.IGNORECASE)
_BAD_TERMS = ("music", "song", "vlog", "reaction", "funny", "prank", "asmr", "shorts", "compilation")

_STOP_QUESTION_WORDS = re.compile(
    r"\b(what|which|how|when|where|why|who|whom|whose|can|should|could|would|do|does|did|is|are|was|were|to|from|for|on|of|in|at|by|with|your|my|the|a|an|and|or)\b",
    re.IGNORECASE,
)


def _sanitize_query(q: str) -> str:
    q = (q or "").strip()
    if not q:
        return ""
    ok = "".join(_SAFE_WORDS.findall(q))
    return ok or q


def _clean_question_query(q: str) -> str:
    q0 = (q or "").lower().strip()
    if not q0:
        return ""
    q1 = _STOP_QUESTION_WORDS.sub(" ", q0)
    q1 = re.sub(r"[^a-z0-9\s\-\/]", " ", q1)
    q1 = re.sub(r"\s+", " ", q1).strip()
    base_terms = ["grit", "sand", "paint", "wood"]
    tokens = q1.split()
    have = set(tokens)
    for t in base_terms:
        if t not in have:
            tokens.append(t)
    seen = set()
    cleaned_tokens: List[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            cleaned_tokens.append(t)
    return " ".join(cleaned_tokens).strip()


# ============================================================
# ✅ Умное сравнение по ключевым словам (3→2→1 совпадение)
# ============================================================
def _has_keyword(primary_keyword: str, title: str, desc: str, min_matches: int = 2) -> int:
    """Возвращает количество найденных совпадений.
    min_matches используется при фильтрации."""
    if not primary_keyword:
        return 0
    text = f"{title} {desc}".lower()
    tokens = [t for t in re.split(r"\W+", primary_keyword.lower()) if len(t) >= 3]
    if not tokens:
        return 0
    match_count = sum(1 for t in tokens if t in text)
    return match_count


# ========== CORE SEARCH ==========
def search_youtube_by_query(query: str, max_results: int = 8) -> List[Dict]:
    yt = _get_youtube()
    q = _sanitize_query(query)
    if not q:
        return []
    print(f"[eQualle VideoFeed][QUERY] 🔍 Searching YouTube for: '{q}'")
    try:
        req = yt.search().list(
            part="snippet",
            q=q,
            type="video",
            maxResults=max_results,
            relevanceLanguage="en",
            videoDuration="medium",
            videoEmbeddable="true",
            safeSearch="moderate",
            order="relevance",
        )
        resp = req.execute()
    except HttpError as e:
        print(f"[eQualle VideoFeed][ERROR] HTTP error for '{q}': {e}")
        return []
    except Exception as e:
        print(f"[eQualle VideoFeed][ERROR] Unexpected error for '{q}': {e}")
        return []

    out: List[Dict] = []
    for it in resp.get("items", []):
        vid = it.get("id", {}).get("videoId", "")
        sn = it.get("snippet", {}) or {}
        if not vid or not sn.get("title"):
            continue
        out.append({
            "id": vid,
            "title": html.unescape(sn.get("title", "").strip()),
            "link": f"https://www.youtube.com/watch?v={vid}",
            "published": sn.get("publishedAt", "").strip(),
            "description": html.unescape(sn.get("description", "").strip()),
        })
    print(f"[eQualle VideoFeed][QUERY] 📋 Parsed {len(out)} results for '{q}'")
    return out


# ========== STATE HELPERS ==========
def _state_path() -> Path:
    return _BLOG_SRC_DIR / "data" / "video_state.json"

def _safe_read_state() -> Dict[str, List[str]]:
    p = _state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"used": []}
    return {"used": []}

def _safe_write_state(state: Dict[str, List[str]]) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ========== SMART SEARCH ==========
def search_youtube_smart(topic_title: str, primary_keyword: str, kw_slug: str, max_results: int = 25) -> List[Dict]:
    all_results: List[Dict] = []

    # читаем used video IDs
    state = _safe_read_state()
    used_ids = set(state.get("used", []))
    print(f"[eQualle VideoFeed][STATE] 📒 Loaded {len(used_ids)} used video IDs from state file")

    cleaned_title = _clean_question_query(topic_title)
    if cleaned_title:
        print(f"[eQualle VideoFeed][SMART] 🧹 Cleaned title query → '{cleaned_title}'")
        title_results = search_youtube_by_query(cleaned_title, max_results)
        for r in title_results:
            r["source"] = "title"
        all_results += title_results
    else:
        title_query = _sanitize_query(topic_title)
        if title_query:
            print(f"[eQualle VideoFeed][SMART] 🧩 Search by raw title: '{title_query}'")
            title_results = search_youtube_by_query(title_query, max_results)
            for r in title_results:
                r["source"] = "title"
            all_results += title_results

    if primary_keyword:
        keyword_query = _sanitize_query(primary_keyword)
        if keyword_query:
            print(f"[eQualle VideoFeed][SMART] ➕ Adding keyword search: '{keyword_query}'")
            kw_results = search_youtube_by_query(keyword_query, max_results)
            for r in kw_results:
                r["source"] = "keyword"
            all_results += kw_results

    # удаляем дубли и уже использованные ID
    seen = set()
    unique = []
    for v in all_results:
        vid = v.get("id")
        if not vid or vid in seen:
            continue
        if vid in used_ids:
            print(f"[eQualle VideoFeed][FILTER] ⏭️ Skip already used video ID: {vid}")
            continue
        seen.add(vid)
        unique.append(v)
        if len(unique) >= max_results:
            break

    print(f"[eQualle VideoFeed][SMART] ✅ Total unique (unused): {len(unique)} after filtering.")
    return unique


# ========== ENRICH ==========
def enrich_video_info(video: Dict) -> Dict:
    raw_title = html.unescape((video.get("title") or "").strip())
    desc = html.unescape((video.get("description") or "").strip())
    words = raw_title.split()
    short_title = " ".join(words[:3]) if len(words) >= 3 else raw_title
    section_title = f"{short_title} — Video Guide" if raw_title else "Video Guide"
    sentences = desc.split(". ")
    desc_short = ". ".join(sentences[:3]) + "." if len(sentences) > 1 else desc
    if len(desc_short) > 600:
        desc_short = desc_short[:600].rsplit(".", 1)[0] + "."
    enriched = {
        **video,
        "section_title": section_title,
        "video_description": desc_short,
        "video_title_rewritten": raw_title,
    }
    print(f"[eQualle VideoFeed][ENRICH] ✨ {enriched.get('id', '?')} → '{enriched['video_title_rewritten']}' ({len(desc_short)} chars)")
    return enriched


# ========== MAIN LOGIC ==========
def find_video_for_article(topic_title: str, primary_keyword: str, kw_slug: str, embedded_video_id: Optional[str] = None) -> Optional[Dict]:
    print(f"\n[eQualle VideoFeed][START] 🎬 Looking for video → '{topic_title}' | KW='{primary_keyword}' | Cat='{kw_slug}'")
    if embedded_video_id:
        print(f"[eQualle VideoFeed][FOUND] 🎯 Embedded ID found → {embedded_video_id}")
        video = {
            "id": embedded_video_id,
            "title": "",
            "link": f"https://www.youtube.com/watch?v={embedded_video_id}",
            "published": "",
            "description": "",
        }
        return enrich_video_info(video)
    if not YT_API_KEY:
        print("[eQualle VideoFeed][ERROR] ❌ No API key — cannot perform search.")
        return None
    try:
        results = search_youtube_smart(topic_title, primary_keyword, kw_slug)
        print(f"[eQualle VideoFeed][DEBUG] Got {len(results)} candidates.")

        # Пробуем последовательно 3 → 2 → 1 совпадение
        for min_match in (3, 2, 1):
            print(f"[eQualle VideoFeed][FILTER] 🔍 Trying match level ≥{min_match}")
            for v in results:
                title_lower = (v.get("title", "") or "").lower()
                desc_lower = (v.get("description", "") or "").lower()
                video_link = v.get("link", f"https://www.youtube.com/watch?v={v.get('id','')}")
                if any(bad in title_lower for bad in _BAD_TERMS):
                    print(f"[eQualle VideoFeed][FILTER] ⏭️ Skip (bad term) '{v['title'][:40]}' — {video_link}")
                    continue
                if len(desc_lower) < 5:
                    print(f"[eQualle VideoFeed][FILTER] ⏭️ Skip (too short) '{v['title'][:40]}' — {video_link}")
                    continue
                matches = _has_keyword(primary_keyword, title_lower, desc_lower)
                if matches < min_match:
                    print(f"[eQualle VideoFeed][FILTER] ⏭️ Skip (no match≥{min_match}) '{v['title'][:40]}' — {video_link}")
                    continue
                print(f"[eQualle VideoFeed][RESULT] ✅ Selected video: '{v['title']}' — {video_link}")
                print(f"[eQualle VideoFeed][RESULT] 🔎 Found via: {v.get('source', 'unknown')} | Keyword matches: {matches}")
                print(f"[eQualle VideoFeed][RESULT] 💡 Match threshold met: ≥{min_match}")

                # сохраняем выбранный ID в video_state.json
                state = _safe_read_state()
                used_ids = set(state.get("used", []))
                vid = v.get("id")
                if vid and vid not in used_ids:
                    used_ids.add(vid)
                    state["used"] = list(used_ids)
                    _safe_write_state(state)
                    print(f"[eQualle VideoFeed][STATE] 💾 Saved used video ID: {vid}")

                return enrich_video_info(v)
        print("[eQualle VideoFeed][WARN] ⚠️ No suitable YouTube result found at any level.")
    except Exception as e:
        print(f"[eQualle VideoFeed][ERROR] ❌ Exception during YouTube search: {e}")
    print("[eQualle VideoFeed][END] 🚫 No video selected — returning None.")
    return None
