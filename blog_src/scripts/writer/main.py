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
from .llm import call_llm as call_llm_local
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

# === Social cards integration ===
from .social_cards import generate_cards_and_update_markdown

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
    """
    Приводит заголовок к Title Case, при этом сохраняет акронимы из исходной строки (например, DIY, UV).
    """
    base = re.sub(r"\s+", " ", (text or "").strip())
    tc = base.title()
    # восстановим акронимы (2+ символов в UPPERCASE) из оригинала
    for w in set(re.findall(r"\b[0-9A-Z]{2,}\b", base)):
        tc = re.sub(rf"\b{re.escape(w.title())}\b", w, tc)
    return tc

def _clean_meta_description(desc: str, title: str) -> str:
    """
    Чистим META_DESCRIPTION: убираем повтор заголовка в начале, ограничиваем ~160 символами по слову.
    """
    if not desc:
        return ""
    s = desc.strip().strip('"').strip()
    # если начинается с заголовка — убираем его
    if s.lower().startswith((title or "").strip().lower()):
        s = s[len(title):].lstrip(" —:|,.-")
    # ограничение 160 символов без обрыва слова
    max_len = 160
    if len(s) > max_len:
        cut = s[:max_len]
        last_space = cut.rfind(" ")
        if last_space > 60:  # чтобы не обрубить слишком коротко
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
    """
    Создаёт content/categories/<slug>/_index.md если отсутствует.
    Это нужно, чтобы категории не попадали в директорию постов.
    """
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
    """
    На всякий случай удаляем любые секции вида '## Video...' из LLM-текста,
    если видео не найдено (чтобы не появлялась пустая секция).
    """
    pattern = re.compile(r"(?mi)^\s*##\s*video[^\n]*\n(?:.*\n)*?(?=^\s*##\s+|\Z)")
    new_md = re.sub(pattern, "", md)
    if new_md != md:
        print("[eQualle VIDEO][CLEAN] 🧹 Removed stray LLM 'Video' section (no video selected).")
    return new_md

def _inject_iframe_before_faq_or_end(article_md: str, video_iframe: str) -> tuple[str, str]:
    """
    Вставляет iframe:
      1) ПЕРЕД секцией FAQ (## Frequently Asked Questions | ## FAQ)
      2) Иначе — в конец статьи
    Возвращает (новый_md, стратегия)
    """
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

# === УНИВЕРСАЛЬНОЕ ОПРЕДЕЛЕНИЕ КОРНЯ ПРОЕКТА (Windows, локально, GitHub Actions) ===
def _detect_project_root(this_file: Path) -> Path:
    # 1) Предпочтительно: найти .git у ближайшего родителя
    for p in this_file.parents:
        if (p / ".git").exists():
            return p

    # 2) Частный случай GitHub Actions: /home/runner/work/<repo>/<repo>/...
    #    Нужно вернуть /home/runner/work/<repo>
    parts = this_file.parts
    if "work" in parts:
        try:
            i = parts.index("work")
            # /home/runner/work/<repo>
            repo = parts[i + 1]
            return Path("/").joinpath(*parts[: i + 2])
        except Exception:
            pass

    # 3) Если каталог репозитория встречается среди родителей по имени
    for p in this_file.parents:
        if p.name == "blog.equalle.com":
            return p

    # 4) Фолбэк: как было раньше (но аккуратнее — не жёстко 3 уровня)
    #    Ищем родителя, где есть blog_src — это стабильный ориентир.
    for p in this_file.parents:
        if (p / "blog_src").exists():
            return p

    # 5) Самый последний фолбэк — вернуть родителя на несколько уровней вверх
    return this_file.parents[3]  # соответствует прежней логике

def _ci_persist_author_state(data_dir: Path) -> None:
    """
    Сохраняет обновлённый author_state.json обратно в репозиторий при запуске в CI.
    Коммит помечен [skip ci], чтобы не создавать бесконечные билды.
    Безопасно игнорирует ошибки (не валит пайплайн).
    """
    try:
        if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
            print("[eQualle AUTHOR][SYNC] ℹ️ Not in CI — skip persist.")
            return

        author_state_file = data_dir / "author_state.json"
        if not author_state_file.exists():
            print("[eQualle AUTHOR][SYNC] ⚠️ author_state.json not found — nothing to persist.")
            return

        # Настройка git user для CI
        subprocess.run(
            ["git", "config", "--global", "user.email", "equalle-bot@users.noreply.github.com"],
            check=False,
        )
        subprocess.run(
            ["git", "config", "--global", "user.name", "eQualle Bot"],
            check=False,
        )

        # Добавляем и коммитим состояние
        subprocess.run(["git", "add", str(author_state_file)], check=False)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "🌀 Rotate author (CI state) [skip ci]",
                "--allow-empty",
            ],
            check=False,
        )

        # Пушим в текущую ветку (обычно main)
        branch = os.environ.get("GITHUB_REF_NAME", "main")
        subprocess.run(["git", "push", "origin", branch], check=False)

        print("[eQualle AUTHOR][SYNC] ✅ Author rotation state persisted to repo.")
    except Exception as e:
        print(f"[eQualle AUTHOR][SYNC][FAIL] ❌ {e}")

def main() -> None:
    print("────────────────────────────────────────────")
    print("[eQualle Writer][INIT] 🚀 Starting in CSE seed→longtail mode (CI)")

    # В онлайне используем общий загрузчик конфигурации
    cfg = load_writer_config()

    # Абсолютные пути для стабильной работы в CI/CD (универсально)
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
    if content_dir.exists():
        print(f"[eQualle PATH][ABS]   content_dir={content_dir.resolve()}")

    # === Автор ===
    author_name, author_style = _pick_next_author(data_dir)
    print(f"[eQualle AUTHOR][PICK] ✍️ {author_name}")

    # === Пара core→longtail из categories.json ===
    cat, seed, longtail = get_next_pair(categories_path, state_path)
    print("────────────────────────────────────────────")
    print(f"[eQualle PAIR][SELECT] 📌 Category={cat.name} ({cat.slug})")
    print(f"[eQualle PAIR][SEED]   🌱 Seed={seed}")
    print(f"[eQualle PAIR][LONG]   🔎 LongTail={longtail}")
    _ensure_category_index(category_dir, cat.slug, cat.name)

    # === Источники (Google CSE) ===
    print("[eQualle CSE][FETCH] 🌐 Querying Google CSE…")
    results = fetch_sources(
        seed,
        longtail,
        n=int(cfg.get("google_cse", {}).get("results", 6)),
        gl=cfg.get("google_cse", {}).get("gl", "us"),
        lr=cfg.get("google_cse", {}).get("lr", "lang_en"),
    )
    print(f"[eQualle CSE][RESULT] 🔗 {len(results)} sources fetched.")
    for i, r in enumerate(results, 1):
        print(f"   [{i}] {r['title']} — {r['url']}")
    sources_summary = build_sources_summary(results)
    print(f"[eQualle CSE][SUMMARY] 📄 {len(sources_summary)} chars summary built.")

    original_url = results[0]["url"] if results else ""
    if original_url:
        print(f"[eQualle CSE][ORIGINAL] 🌐 Primary source → {original_url}")
    else:
        print("[eQualle CSE][ORIGINAL] ⚠️ No source URL found (empty results).")

    # === Видео (YouTube API), только выбор. НИЧЕГО из summary здесь не используется. ===
    video_payload: Optional[dict] = None
    video_iframe: str = ""
    if find_video_for_article:
        print("[eQualle VIDEO][FIND] 🎞️ Looking up YouTube video…")
        try:
            v = find_video_for_article(
                topic_title=longtail,
                primary_keyword=seed,
                kw_slug=_slugify(cat.slug),
            )
            if v and isinstance(v, dict) and v.get("id"):
                st_raw = (v.get("section_title") or "").strip()
                if len(st_raw) < 8:
                    v["section_title"] = _make_section_title(v)
                video_payload = {
                    "id": v.get("id", ""),
                    "title": v.get("title", ""),
                    "video_title_rewritten": v.get("video_title_rewritten", ""),
                    "link": v.get("link", ""),
                    "published": v.get("published", ""),
                    "video_description": v.get("video_description") or v.get("description", ""),
                    "section_title": v.get("section_title"),
                }
                print(f"[eQualle VIDEO][OK] ✅ Selected '{(video_payload.get('video_title_rewritten') or video_payload.get('title') or '')[:80]}' ({video_payload['id']})")
            else:
                print("[eQualle VIDEO][MISS] 🚫 No suitable video found.")
        except Exception as e:
            print(f"[eQualle VIDEO][FAIL] ⚠️ {e}")
    else:
        print("[eQualle VIDEO][SKIP] ℹ️ find_video_for_article unavailable; skipping.")

    # === Prompt ===
    print("[eQualle PROMPT][START] ✍️ Building prompt…")
    prompt = build_prompt(
        topic=longtail,
        summary=sources_summary,
        original_url=original_url,
        video=video_payload,            # None если видео нет — и LLM не станет писать секцию
        style_hint=author_style,
        main_kw=seed or longtail,       # главный ключ — seed (core), fallback — longtail
    )
    print(f"[eQualle PROMPT][OK] ✅ Using custom prompt_builder ({len(prompt)} chars).")

    # === Генерация ===
    print("[eQualle LLM][CALL] 🧠 Invoking local LLM once…")
    article_md: str = call_llm_local(prompt)
    print(f"[eQualle LLM][RETURN] 📜 {len(article_md)} chars generated.")

    # === ИЗВЛЕЧЕНИЕ META_DESCRIPTION из текста LLM (и удаление из тела) ===
    meta_desc = ""
    md_meta_match = re.search(r"(?mi)^\s*META_DESCRIPTION:\s*(.+)$", article_md)
    if md_meta_match:
        raw_meta = md_meta_match.group(1).strip()
        page_title_tc_for_meta = _title_case(longtail)
        meta_desc = _clean_meta_description(raw_meta, page_title_tc_for_meta)
        article_md = re.sub(r"(?mi)^\s*META_DESCRIPTION:.*\n?", "", article_md)
        print(f"[eQualle META][OK] 📝 Extracted description ({len(meta_desc)} chars).")

    # === Чистка двойных видео-секций ===
    if video_payload:
        extracted = _extract_video_description_from_md(article_md, video_payload)
        if extracted:
            video_payload["video_description"] = extracted[:500].strip()
            print(f"[eQualle VIDEO][DESC] ✂️ Extracted from LLM: {video_payload['video_description'][:100]}...")
        article_md = _strip_llm_video_section(article_md, video_payload)
    else:
        article_md = _strip_any_llm_video_sections(article_md)

    # === Вставка iframe (ТОЛЬКО если видео найдено) — ПЕРЕД FAQ, иначе в конец ===
    if video_payload:
        try:
            video_iframe = build_video_embed(video_payload)
            article_md, strategy = _inject_iframe_before_faq_or_end(article_md, video_iframe)
            print(f"[eQualle VIDEO][EMBED] ✅ Iframe injection strategy: {strategy}")
            # Product link — вставляем ТОЛЬКО если был вставлен блок видео (как раньше)
            try:
                article_md = inject_product_link_after_video_source(
                    article_md,
                    context=f"{cat.name} | {seed} | {longtail}",
                )
                print("[eQualle LINK][OK] 🔗 Product link injected after 'Video source:'.")
            except Exception as e:
                print(f"[eQualle LINK][FAIL] ⚠️ {e}")
        except Exception as e:
            print(f"[eQualle VIDEO][EMBED][FAIL] ⚠️ {e}")
    else:
        print("[eQualle VIDEO][EMBED][SKIP] ℹ️ No video — no section, no product-link anchor.")

    # === QA + Brand images ===
    qa_result = posts.qa_check_proxy(article_md)
    if not qa_result.get("ok"):
        print(f"[eQualle QA][FAIL] ⚠️ {qa_result.get('errors')}")
        _save_draft(content_dir, longtail)
        return
    print("[eQualle QA][OK] ✅ Passed.")
    article_md = inject_brand_images(article_md)

    # === ⬇️ ПАТЧ: найти ПЕРВУЮ бренд-картинку, чтобы записать её в front matter (для RSS) ===
    image_url = None
    try:
        m = re.search(r'(https?://blog\.equalle\.com)?/images/brand/[^\s)\"\\\']+\.(?:webp|jpg|jpeg|png)', article_md)
        if m:
            image_url = m.group(0)
            if not image_url.startswith("http"):
                image_url = f"https://blog.equalle.com{image_url}"
            print(f"[eQualle IMAGE][OK] 🖼️ First brand image for RSS → {image_url}")
        else:
            print("[eQualle IMAGE][MISS] ℹ️ No brand image found in article body.")
    except Exception as e:
        print(f"[eQualle IMAGE][FAIL] ⚠️ {e}")

    # === Теги ===
    try:
        auto_tags = build_tags(body_text=article_md, category_name=cat.name, max_tags=10)
    except Exception:
        auto_tags = []
    print(f"[eQualle TAGS][OK] 🏷️ {auto_tags}")

    # === Сохранение поста ===
    now = datetime.now(timezone.utc)
    slug_source = f"{longtail} {seed}".strip()
    safe_slug = _safe_slug_from_string(posts.make_slug(slug_source))
    out_path = content_dir / f"{now.year}/{now.month:02d}/{safe_slug}.md"
    _ensure_dir(out_path.parent)

    # Title → Title Case
    title_tc = _title_case(longtail)
    title_escaped = title_tc.replace('"', '\\"')

    tags_yaml = ", ".join("'" + t.replace("'", "''") + "'" for t in auto_tags or [])
    categories_line = f"categories: ['{cat.name}']"

    # description (если вытащили из META_DESCRIPTION)
    description_line = ""
    if meta_desc:
        # безопасное экранирование кавычек для YAML-строки
        safe_meta = meta_desc.replace('"', '\\"')
        description_line = f'description: "{safe_meta}"\n'

    # ⬇️ добавляем image_line, только если нашли картинку
    image_line = f'image: "{image_url}"\n' if image_url else ""

    fm = (
        "---\n"
        f'title: "{title_escaped}"\n'
        f"date: {now.isoformat()}\n"
        "draft: false\n"
        f'slug: "{safe_slug}"\n"
        f"{categories_line}\n"
        f"tags: [{tags_yaml}]\n"
        f'author: "{author_name}"\n'
        f"{image_line}"
        f"{description_line}"
        "---\n\n"
    )
    with out_path.open("w", encoding="utf-8") as f:
        f.write(fm + article_md.strip() + "\n")

    print("🧾 Front-matter preview:")
    print(fm)
    print(f"[eQualle SAVE][OK] ✅ {out_path}")

    # === Генерация соц-карточек и обновление front matter ===
    try:
        generate_cards_and_update_markdown(
            slug=safe_slug,
            title=title_tc,
            date=now,
            md_path=out_path,
        )
    except Exception as e:
        print(f"[eQualle CARDS][WARN] ⚠️ Failed to generate social cards: {e}")

    # === Обновляем state для пары ===
    record_used_pair(state_path, seed, longtail)
    print("[eQualle STATE][OK] 💾 Pair recorded.")

    # === Сохраняем ротацию автора в репозиторий (только в CI) ===
    _ci_persist_author_state(data_dir)

    print("────────────────────────────────────────────")
    print("[eQualle DONE] 🎉 All steps completed successfully.")
    print(f"[eQualle OUTPUT] 📄 {out_path}")

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
