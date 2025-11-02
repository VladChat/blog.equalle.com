# blog_src/scripts/writer/rss_fetch.py
# -*- coding: utf-8 -*-
"""
Unified RSS picker with categories-based keywords.

Key features:
- Loads keywords from blog_src/data/categories.json via topics.py
- Rotates through RSS feeds (state.json: last_rss) and uses category-first keyword rotation (in topics.py)
- Deduplicates by normalized link in state['seen']
- Returns (topic, summary, original_url, keyword, category_name, category_slug)
- Verbose logs matching existing style
"""
from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import feedparser  # type: ignore
except Exception:
    feedparser = None

DATA_DIR = Path("blog_src/data")
RSS_FILE = DATA_DIR / "rss.json"
STATE_FILE = DATA_DIR / "state.json"

# Import keyword/category logic
from .topics import load_keywords_and_topics, get_next_keyword_and_category


def _load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📥 Loaded JSON: {path.as_posix()} (size={len(json.dumps(data, ensure_ascii=False))} chars)")
        return data
    except FileNotFoundError:
        print(f"ℹ️ {path.name} not found, using default.")
        return default
    except Exception as e:
        print(f"⚠️ Failed to read {path.name}: {e} — using default.")
        return default


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved JSON: {path.as_posix()}")


def _normalize_url(u: str) -> str:
    u = (u or "").strip()
    u = re.sub(r"#.*$", "", u)
    u = re.sub(r"/+$", "", u)
    return u


def _extract_feeds(data) -> list[str]:
    if isinstance(data, list):
        return [str(x).strip() for x in data if str(x).strip()]
    if isinstance(data, dict) and "feeds" in data:
        return [str(x).strip() for x in data["feeds"] if str(x).strip()]
    return []


def _entry_summary(entry) -> str:
    for key in ("summary", "description", "content"):
        v = entry.get(key)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, list) and v and isinstance(v[0], dict) and v[0].get("value"):
            return v[0]["value"]
    return ""


def get_latest_topic():
    # Load state and inputs
    state = _load_json(STATE_FILE, {"last_rss": -1, "seen": []})
    rss_data = _load_json(RSS_FILE, [])
    feeds = _extract_feeds(rss_data)

    # Only for stats in logs (we don't use this list for rotation anymore)
    keywords_flat, _topics_flat = load_keywords_and_topics()

    print("───────────────────────────────")
    print("🚀 RSS Picker starting")
    print(f"📚 RSS sources: {len(feeds)} | 🧠 seen cache: {len(state.get('seen', []))} | 🔑 keywords: {len(keywords_flat)}")

    if not feeds or feedparser is None:
        print("⚠️ No feeds configured or feedparser not available.")
        # Return full 6-tuple (placeholders for keyword/category)
        return "Daily eQualle Update", "", None, "", None, ""

    # Rotation index for feeds
    last_rss = int(state.get("last_rss", -1))
    next_rss = (last_rss + 1) % len(feeds) if feeds else 0

    print(f"🔁 Start rotation from RSS index: {next_rss} (mod {len(feeds)})")

    chosen = None
    chosen_feed_idx = None
    for step in range(len(feeds)):
        feed_idx = (next_rss + step) % len(feeds)
        feed_url = feeds[feed_idx]
        print("───────────────────────────────")
        print(f"🌐 Checking RSS feed [{feed_idx}]: {feed_url}")
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"⚠️ feedparser error: {e}")
            continue

        entries = getattr(parsed, "entries", []) or []
        print(f"📦 Entries found: {len(entries)}")
        new_entry = None
        skipped = 0
        seen_set = set(_normalize_url(s) for s in state.get("seen", []))

        for entry in entries:
            link = _normalize_url(str(entry.get("link", "")))
            if not link:
                skipped += 1
                continue
            if link in seen_set:
                skipped += 1
                continue
            new_entry = entry
            break

        if new_entry:
            chosen = new_entry
            chosen_feed_idx = feed_idx
            print(f"✅ Selected NEW article after checking {skipped + 1} entries (skipped {skipped}) in feed [{feed_idx}]")
            break
        else:
            print(f"⏭️ No new entries in feed [{feed_idx}] (skipped {skipped})")

    if not chosen:
        print("⚠️ No new articles found in all feeds — returning placeholder.")
        # Return full 6-tuple (placeholders for keyword/category)
        return "Daily eQualle Update", "", None, "", None, ""

    # Compose output from chosen entry
    topic = str(chosen.get("title", "") or "").strip() or "Daily eQualle Update"
    summary = _entry_summary(chosen)
    orig_link = _normalize_url(str(chosen.get("link", "")).strip()) or None

    # Advance feed rotation & update seen
    state["last_rss"] = int(chosen_feed_idx if chosen_feed_idx is not None else next_rss)
    if orig_link:
        seen = state.get("seen", [])
        seen.append(orig_link)
        # keep last 500 seen
        state["seen"] = seen[-500:]
    _save_json(STATE_FILE, state)

    # Keyword + category (category-first rotation handled inside topics.py)
    keyword, kw_cat, kw_slug = get_next_keyword_and_category()

    print("───────────────────────────────")
    print(f"📰 RSS Source: {feeds[state['last_rss']] if feeds else '(none)'}")
    print(f"🧩 Topic: {topic}")
    print(f"📄 Summary: {summary[:250]}{'...' if len(summary) > 250 else ''}")
    print(f"🔗 Link: {orig_link}")
    print(f"🎯 Using keyword: {keyword} | category: {kw_cat or '(auto)'} ({kw_slug})")
    print(f"🔄 last_rss -> {state['last_rss']}")
    print(f"🗂 seen size -> {len(state.get('seen', []))}")
    print("───────────────────────────────")

    # Return: provide topic, summary, link, plus keyword and its category/slug
    return topic, summary, orig_link, keyword, kw_cat, kw_slug


# For standalone quick check
if __name__ == "__main__":
    get_latest_topic()
