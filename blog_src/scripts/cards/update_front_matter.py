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
    return [
        p for p in CONTENT_ROOT.rglob("*.md")
        if p.name != "index.md"
    ]


def parse_post_date(md_path: Path) -> datetime | None:
    """Читает дату из front matter."""
    try:
        fm = frontmatter.load(md_path)
        raw = fm.get("date")
        if isinstance(raw, datetime):
            return raw
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None


def build_card_urls(md_path: Path, slug: str) -> dict:
    """
    Делаем ссылки по актуальной структуре:
    /YYYY/MM/DD/<slug>/cards/<platform>/<slug>.jpg
    """
    # путь типа: /posts/2025/11/20/<slug>
    rel_post_dir = "/" + str(md_path.parent.relative_to(CONTENT_ROOT.parent)).replace("\\", "/")

    # путь карточек: /posts/YYYY/MM/DD/<slug>/cards/<platform>/<slug>.jpg
    cards_base = f"{rel_post_dir}/{slug}/cards"

    return {
        "facebook":  f"{cards_base}/facebook/{slug}.jpg",
        "twitter":   f"{BASE_URL}{cards_base}/facebook/{slug}.jpg",
        "instagram": f"{cards_base}/instagram/{slug}.jpg",
        "pinterest": f"{cards_base}/pinterest/{slug}.jpg",
    }


def cards_exist(md_path: Path, slug: str) -> bool:
    """
    Проверяем существование карточек по реальной структуре:
    md_path.parent / slug / cards / <platform> / slug.jpg
    """
    cards_root = md_path.parent / slug / "cards"

    needed = [
        cards_root / "facebook" / f"{slug}.jpg",
        cards_root / "instagram" / f"{slug}.jpg",
        cards_root / "pinterest" / f"{slug}.jpg",
    ]

    return all(p.exists() for p in needed)


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

    # сортируем последние 5
    dated = []
    for md in posts:
        dt = parse_post_date(md)
        if dt:
            dated.append((dt, md))

    dated.sort(key=lambda x: x[0], reverse=True)
    latest_posts = [md for _, md in dated[:5]]

    print("[info] Latest 5 posts to update:")
    for p in latest_posts:
        print(" -", p)

    for md in latest_posts:
        update_front_matter(md)


if __name__ == "__main__":
    main()
