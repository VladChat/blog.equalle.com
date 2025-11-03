# ============================================================
# File: blog_src/scripts/writer/main.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\main.py
# ============================================================

from __future__ import annotations

import json
import re
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# === Core helpers (shared with local writer) ===
from .prompt_builder import build_prompt
from .video_helpers import (
    _make_section_title,
    _extract_video_description_from_md,
    _strip_llm_video_section,
)
from .llm_client import call_llm_local
from .brandimg_injector import inject_brand_images
from .taxonomy.auto_tag import build_tags
from .video_utils import build_video_embed
from .link_injector import inject_product_link_after_video_source  # вставляем ТОЛЬКО если есть видео
from . import posts  # для QA (qa_check_proxy)

# === New architecture sources (CSE + YouTube) ===
from .topics_pairs import get_next_pair, record_used_pair     # берём core→longtail из categories.json
from .google_cse import fetch_sources, build_sources_summary  # Google CSE вместо RSS-статьи
try:
    from .rss_video_fetch import find_video_for_article       # YouTube API (не RSS)
except Exception:
    find_video_for_article = None

# === Online config (CI/CD) ===
from .config_loader import load_writer_config  # используем общий загрузчик конфигурации для онлайн-среды

# === Авторская ротация (как в локальной версии) ===
AUTHORS = [
    {
        "name": "Mark Jensen",
        "style": (
            "You are Mark Jensen — Senior Technical Writer for eQualle Blog. "
            "Write in a precise, professional, and highly technical tone. "
            "Focus on surface preparation, abrasive performance, and sanding workflows. "
            "Use expert terminology but keep explanations clear for advanced readers."
        ),
    },
    {
        "name": "David Chen",
        "style": (
            "You are David Chen — Product Engineer & Reviewer for eQualle Blog. "
            "Write analytically and fact-based, like an engineer reviewing tools. "
            "Emphasize testing, performance evaluation, and material science behind abrasives. "
            "Use objective comparisons and reliable data."
        ),
    },
    {
        "name": "Lucas Moreno",
        "style": (
            "You are Lucas Moreno — Workshop & DIY Specialist for eQualle Blog. "
            "Write in a confident, hands-on, and workshop-oriented tone. "
            "Give step-by-step project instructions, practical tips, and real-life sanding advice "
            "for hobbyists and professionals alike."
        ),
    },
    {
        "name": "Emily Novak",
        "style": (
            "You are Emily Novak — Content Editor & Research Lead for eQualle Blog. "
            "Write in a calm, educational, and reader-focused tone. "
            "Prioritize clarity, organization, and helpful explanations. "
            "Bridge technical depth with accessible language for general audiences."
        ),
    },
]

# === Helpers: TitleCase и Meta Description ===
def _title_case(text: str) -> str:
    base = re.sub(r"\s+", " ", (text or "").strip())
    tc = base.title()
    for w in set(re.findall(r"\b[0-9A-Z]{2,}\b", base)):
        tc = re.sub(rf"\b{re.escape(w.title())}\b", w, tc)
    return tc

def _clean_meta_description(desc: str, title: str) -> str:
    if not desc:
        return ""
    s = desc.strip().strip('"').strip()
    if s.lower().startswith((title or "").strip().lower()):
        s = s[len(title):].lstrip(" —:|,.-")
    max_len = 160
    if len(s) > max_len:
        cut = s[:max_len]
        last_space = cut.rfind(" ")
        if last_space > 60:
            cut = cut[:last_space]
        s = cut
    return s

def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\-\s]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80] if len(s) > 80 else s

def _safe_slug_from_string(text: str) -> str:
    base = re.sub(r"(\d+)x(\d+)", r"\1-by-\2", text)
    base = re.sub(r"[^a-zA-Z0-9\-]+", "-", base)
    base = re.sub(r"-+", "-", base).strip("-").lower()
    return base

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _ensure_category_index(category_dir: Path, cat_slug: str, cat_name: str) -> None:
    idx = category_dir / cat_slug / "_index.md"
    if not idx.exists():
        _ensure_dir(idx.parent)
        fm = (
            "---\n"
            f'title: "{cat_name}"\n'
            "layout: list\n"
            "---\n"
        )
        idx.write_text(fm, encoding="utf-8")
        print(f"[eQualle CATEGORY][CREATE] ✅ {idx}")

def _strip_any_llm_video_sections(md: str) -> str:
    pattern = re.compile(r"(?mi)^\s*##\s*video[^\n]*\n(?:.*\n)*?(?=^\s*##\s+|\Z)")
    new_md = re.sub(pattern, "", md)
    if new_md != md:
        print("[eQualle VIDEO][CLEAN] 🧹 Removed stray LLM 'Video' section (no video selected).")
    return new_md

def _inject_iframe_before_faq_or_end(article_md: str, video_iframe: str) -> tuple[str, str]:
    if not video_iframe:
        return article_md, "skip:no_iframe"
    faq_hdr_re = re.compile(r"(?mi)^\s*##\s*(?:frequently\s+asked\s+questions|faq)\b.*$")
    m_faq = faq_hdr_re.search(article_md)
    if m_faq:
        insert_pos = m_faq.start()
        new_md = article_md[:insert_pos].rstrip() + "\n\n" + video_iframe + "\n\n" + article_md[insert_pos:]
        return new_md, "before_faq"
    return article_md.rstrip() + "\n\n" + video_iframe + "\n", "append_end"

def _pick_next_author(data_dir: Path) -> tuple[str, str]:
    state_path = data_dir / "author_state.json"
    idx = 0
    if state_path.exists():
        try:
            idx = (json.loads(state_path.read_text(encoding="utf-8")).get("index", 0)) % len(AUTHORS)
        except Exception:
            idx = 0
    author = AUTHORS[idx]
    next_idx = (idx + 1) % len(AUTHORS)
    state_path.write_text(json.dumps({"index": next_idx}, ensure_ascii=False, indent=2), encoding="utf-8")
    return author["name"], author["style"]

# === ОПРЕДЕЛЕНИЕ КОРНЯ ПРОЕКТА ===
def _detect_project_root(this_file: Path) -> Path:
    for p in this_file.parents:
        if (p / ".git").exists():
            return p
    parts = this_file.parts
    if "work" in parts:
        try:
            i = parts.index("work")
            repo = parts[i + 1]
            return Path("/").joinpath(*parts[: i + 2])
        except Exception:
            pass
    for p in this_file.parents:
        if p.name == "blog.equalle.com":
            return p
    for p in this_file.parents:
        if (p / "blog_src").exists():
            return p
    return this_file.parents[3]

def _ci_persist_author_state(data_dir: Path) -> None:
    try:
        if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
            print("[eQualle AUTHOR][SYNC] ℹ️ Not in CI — skip persist.")
            return
        author_state_file = data_dir / "author_state.json"
        if not author_state_file.exists():
            print("[eQualle AUTHOR][SYNC] ⚠️ author_state.json not found — nothing to persist.")
            return
        subprocess.run(["git", "config", "--global", "user.email", "equalle-bot@users.noreply.github.com"], check=False)
        subprocess.run(["git", "config", "--global", "user.name", "eQualle Bot"], check=False)
        subprocess.run(["git", "add", str(author_state_file)], check=False)
        subprocess.run(["git", "commit", "-m", "🌀 Rotate author (CI state) [skip ci]", "--allow-empty"], check=False)
        branch = os.environ.get("GITHUB_REF_NAME", "main")
        subprocess.run(["git", "push", "origin", branch], check=False)
        print("[eQualle AUTHOR][SYNC] ✅ Author rotation state persisted to repo.")
    except Exception as e:
        print(f"[eQualle AUTHOR][SYNC][FAIL] ❌ {e}")

def main() -> None:
    print("────────────────────────────────────────────")
    print("[eQualle Writer][INIT] 🚀 Starting in CSE seed→longtail mode (CI)")

    cfg = load_writer_config()
    project_root = _detect_project_root(Path(__file__).resolve())
    content_dir = project_root / cfg.get("content_dir", "blog_src/content/posts")
    category_dir = project_root / cfg.get("category_dir", "blog_src/content/categories")
    data_dir = project_root / cfg.get("data_dir", "blog_src/data")
    categories_path = data_dir / "categories.json"
    state_path = data_dir / "state.json"

    print(f"[eQualle PATH][INFO] content_dir={content_dir}")
    print(f"[eQualle PATH][INFO] category_dir={category_dir}")
    print(f"[eQualle PATH][INFO] data_dir={data_dir}")
    print(f"[eQualle PATH][CHECK] content_dir exists? {content_dir.exists()}")

    author_name, author_style = _pick_next_author(data_dir)
    print(f"[eQualle AUTHOR][PICK] ✍️ {author_name}")

    cat, seed, longtail = get_next_pair(categories_path, state_path)
    print(f"[eQualle PAIR][SELECT] 📌 Category={cat.name} ({cat.slug})")
    print(f"[eQualle PAIR][SEED]   🌱 Seed={seed}")
    print(f"[eQualle PAIR][LONG]   🔎 LongTail={longtail}")
    _ensure_category_index(category_dir, cat.slug, cat.name)

    results = fetch_sources(seed, longtail, n=6, gl="us", lr="lang_en")
    sources_summary = build_sources_summary(results)
    original_url = results[0]["url"] if results else ""

    video_payload: Optional[dict] = None
    if find_video_for_article:
        try:
            v = find_video_for_article(topic_title=longtail, primary_keyword=seed, kw_slug=_slugify(cat.slug))
            if v and v.get("id"):
                video_payload = v
        except Exception as e:
            print(f"[eQualle VIDEO][FAIL] ⚠️ {e}")

    prompt = build_prompt(topic=longtail, summary=sources_summary, original_url=original_url,
                          video=video_payload, style_hint=author_style, main_kw=seed or longtail)
    article_md: str = call_llm_local(prompt)

    meta_desc = ""
    md_meta_match = re.search(r"(?mi)^\s*META_DESCRIPTION:\s*(.+)$", article_md)
    if md_meta_match:
        raw_meta = md_meta_match.group(1).strip()
        meta_desc = _clean_meta_description(raw_meta, _title_case(longtail))
        article_md = re.sub(r"(?mi)^\s*META_DESCRIPTION:.*\n?", "", article_md)

    article_md = _strip_any_llm_video_sections(article_md)
    qa_result = posts.qa_check_proxy(article_md)
    if not qa_result.get("ok"):
        _save_draft(content_dir, longtail)
        return
    article_md = inject_brand_images(article_md)

    now = datetime.now(timezone.utc)
    safe_slug = _safe_slug_from_string(posts.make_slug(f"{longtail} {seed}".strip()))
    out_path = content_dir / f"{now.year}/{now.month:02d}/{safe_slug}.md"
    _ensure_dir(out_path.parent)

    title_tc = _title_case(longtail)
    title_escaped = title_tc.replace('"', '\\"')
    tags_yaml = ""
    categories_line = f"categories: ['{cat.name}']"
    description_line = f'description: "{meta_desc}"\n' if meta_desc else ""

    fm = (
        "---\n"
        f'title: "{title_escaped}"\n'
        f"date: {now.isoformat()}\n"
        "draft: false\n"
        f'slug: \"{safe_slug}\"\n'
        f"{categories_line}\n"
        f"tags: [{tags_yaml}]\n"
        f'author: \"{author_name}\"\n'
        f"{description_line}"
        "---\n\n"
    )
    out_path.write_text(fm + article_md.strip() + "\n", encoding="utf-8")

    record_used_pair(state_path, seed, longtail)
    _ci_persist_author_state(data_dir)
    print(f"[eQualle SAVE][OK] ✅ {out_path}")

def _save_draft(content_dir: Path, topic: str):
    now = datetime.now(timezone.utc)
    fallback_slug = re.sub(r"[^a-zA-Z0-9-]+", "-", topic.lower()) + "-draft"
    out_path = content_dir / f"{now.year}/{now.month:02d}/{fallback_slug}.md"
    _ensure_dir(out_path.parent)
    title_escaped = topic.replace('"', '\\"')
    fm = (
        "---\n"
        f'title: "{title_escaped}"\n'
        f"date: {now.isoformat()}\n"
        "draft: true\n"
        "categories: ['news']\n"
        "tags: ['draft']\n"
        'author: "eQualle Editorial"\n'
        "---\n\n"
        "(Auto-saved draft after QA failure)\n\n"
    )
    out_path.write_text(fm, encoding="utf-8")
    print(f"📝 Draft saved: {out_path}")

if __name__ == "__main__":
    main()
