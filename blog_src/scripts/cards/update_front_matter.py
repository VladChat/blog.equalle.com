# ============================================
# File: blog_src/scripts/cards/update_front_matter.py
# Purpose: Inject social card URLs into Markdown front matter
# Works with single-file posts (*.md) and updates ONLY latest 5 posts
# ============================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import frontmatter

CONTENT_ROOT = Path("blog_src/content/posts")
BASE_URL = "https://blog.equalle.com"


# ========= helpers =========

def _parse_date_value(raw) -> Optional[datetime]:
    """Преобразует значение date из front matter в datetime, если возможно."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        # поддержка формата с Z на конце
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None


# ========= поиск постов и дат =========

def find_all_md_posts() -> List[Path]:
    """Находит ВСЕ .md файлы постов (кроме index.md)."""
    return [
        p for p in CONTENT_ROOT.rglob("*.md")
        if p.name != "index.md"
    ]


def parse_post_date(md_path: Path) -> Optional[datetime]:
    """Читает дату из front matter поста для сортировки."""
    try:
        fm = frontmatter.load(md_path)
    except Exception:
        return None
    return _parse_date_value(fm.get("date"))


# ========= работа с карточками =========

def _cards_root_for(slug: str, date: datetime) -> Path:
    """
    Строит корневую директорию карточек по структуре:

    blog_src/content/posts/YYYY/MM/DD/slug/cards
    """
    y = f"{date.year:04d}"
    m = f"{date.month:02d}"
    d = f"{date.day:02d}"

    return CONTENT_ROOT / y / m / d / slug / "cards"


def cards_exist(slug: str, date: datetime) -> bool:
    """
    Проверяет существование карточек по структуре:
    posts/YYYY/MM/DD/slug/cards/<platform>/<slug>.jpg
    """
    cards_root = _cards_root_for(slug, date)

    needed = [
        cards_root / "facebook" / f"{slug}.jpg",
        cards_root / "instagram" / f"{slug}.jpg",
        cards_root / "pinterest" / f"{slug}.jpg",
    ]

    return all(p.exists() for p in needed)


def build_card_urls(slug: str, date: datetime) -> dict:
    """
    Строит URL'ы карточек по структуре:

    /posts/YYYY/MM/DD/slug/cards/<platform>/<slug>.jpg
    """
    cards_root = _cards_root_for(slug, date)

    # относительный путь "posts/2025/11/20/slug/cards"
    rel_cards = cards_root.relative_to(CONTENT_ROOT.parent).as_posix()
    rel_cards = "/" + rel_cards  # добавить ведущий слэш

    return {
        "facebook":  f"{rel_cards}/facebook/{slug}.jpg",
        "twitter":   f"{BASE_URL}{rel_cards}/facebook/{slug}.jpg",
        "instagram": f"{rel_cards}/instagram/{slug}.jpg",
        "pinterest": f"{rel_cards}/pinterest/{slug}.jpg",
    }


# ========= обновление front matter =========

def update_front_matter(md_path: Path):
    """Добавляет cards: {...} в front matter указанного поста."""
    post = frontmatter.load(md_path)

    slug = post.metadata.get("slug")
    if not slug:
        print(f"[skip] No slug in {md_path}")
        return

    raw_date = post.metadata.get("date")
    date = _parse_date_value(raw_date)
    if not date:
        print(f"[skip] No valid date in {md_path}")
        return

    if not cards_exist(slug, date):
        print(f"[skip] No cards for {slug}")
        return

    card_urls = build_card_urls(slug, date)
    post.metadata["cards"] = card_urls

    # ВАЖНО: используем dumps() → строка → write_text()
    text = frontmatter.dumps(post)
    md_path.write_text(text, encoding="utf-8")

    print(f"[update] Added cards: {slug}")


# ========= main =========

def main():
    posts = find_all_md_posts()
    print(f"[info] Found {len(posts)} markdown posts")

    dated: List[tuple[datetime, Path]] = []
    for md in posts:
        dt = parse_post_date(md)
        if dt:
            dated.append((dt, md))

    # от новых к старым
    dated.sort(key=lambda x: x[0], reverse=True)

    latest_posts = [md for _, md in dated[:5]]

    print("[info] Latest 5 posts to update:")
    for p in latest_posts:
        print(" -", p)

    for md in latest_posts:
        update_front_matter(md)


if __name__ == "__main__":
    main()
