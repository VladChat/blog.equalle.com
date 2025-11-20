# ============================================
# File: blog_src/scripts/cards/update_front_matter.py
# Purpose: Inject social card URLs into Markdown front matter
# Works with single-file posts (*.md) and updates ONLY latest 5 posts
# ============================================

from __future__ import annotations

import frontmatter
from pathlib import Path
from datetime import datetime

CONTENT_ROOT = Path("blog_src/content/posts")
BASE_URL = "https://blog.equalle.com"


def find_all_md_posts() -> list[Path]:
    """Находит ВСЕ .md файлы постов (кроме index.md)."""
    md_files = [
        p for p in CONTENT_ROOT.rglob("*.md")
        if p.name != "index.md"
    ]
    return md_files


def parse_post_date(md_path: Path) -> datetime | None:
    """Читает дату из front matter, чтобы отсортировать посты."""
    try:
        fm = frontmatter.load(md_path)
        raw = fm.get("date")
        if isinstance(raw, datetime):
            return raw
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None


def build_card_urls(md_path: Path, slug: str) -> dict:
    """Строит URL'ы карточек."""
    # относительный путь от корня блога
    rel = "/" + str(md_path.relative_to(CONTENT_ROOT.parent)).replace("\\", "/")

    parent_dir = rel.rsplit("/", 1)[0]  # path without filename

    return {
        "facebook":  f"{parent_dir}/cards/facebook/{slug}.jpg",
        "twitter":   f"{BASE_URL}{parent_dir}/cards/facebook/{slug}.jpg",  # абсолютный путь
        "instagram": f"{parent_dir}/cards/instagram/{slug}.jpg",
        "pinterest": f"{parent_dir}/cards/pinterest/{slug}.jpg",
    }


def cards_exist(md_path: Path, slug: str) -> bool:
    """Проверяет, существуют ли карточки."""
    base = md_path.parent / "cards"

    needed = [
        base / "facebook" / f"{slug}.jpg",
        base / "instagram" / f"{slug}.jpg",
        base / "pinterest" / f"{slug}.jpg",
    ]

    return all(path.exists() for path in needed)


def update_front_matter(md_path: Path):
    """Добавляет cards: {...} в front matter."""
    post = frontmatter.load(md_path)

    slug = post.metadata.get("slug")
    if not slug:
        print(f"[skip] No slug in {md_path}")
        return

    if not cards_exist(md_path, slug):
        print(f"[skip] No cards for {slug}")
        return

    card_urls = build_card_urls(md_path, slug)

    post.metadata["cards"] = card_urls

    with md_path.open("w", encoding="utf-8") as f:
        frontmatter.dump(post, f)

    print(f"[update] Added cards: {slug}")


def main():
    posts = find_all_md_posts()
    print(f"[info] Found {len(posts)} markdown posts")

    # сортируем по дате
    dated = []
    for md in posts:
        dt = parse_post_date(md)
        if dt:
            dated.append((dt, md))

    # от новых к старым
    dated.sort(key=lambda x: x[0], reverse=True)

    # только 5 последних
    latest_posts = [md for _, md in dated[:5]]

    print("[info] Latest 5 posts to update:")
    for p in latest_posts:
        print(" -", p)

    # обновляем только их
    for md in latest_posts:
        update_front_matter(md)


if __name__ == "__main__":
    main()
