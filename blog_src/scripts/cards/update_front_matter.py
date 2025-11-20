# ============================================
# File: blog_src/scripts/cards/update_front_matter.py
# Purpose: Inject social card URLs into Markdown front matter
# ============================================

from __future__ import annotations

import frontmatter
from pathlib import Path

CONTENT_ROOT = Path("blog_src/content/posts")
BASE_URL = "https://blog.equalle.com"


def find_posts() -> list[Path]:
    """Находит все index.md во всех постовых директориях."""
    return list(CONTENT_ROOT.rglob("index.md"))


def build_card_urls(md_path: Path, slug: str) -> dict:
    """
    Строит словарь URL карточек для front matter.
    """

    # /posts/YYYY/MM/DD/slug
    rel = "/" + str(md_path.parent.relative_to(CONTENT_ROOT.parent)).replace("\\", "/")

    return {
        "facebook":   f"{rel}/cards/facebook/{slug}.jpg",
        "twitter":    f"{BASE_URL}{rel}/cards/facebook/{slug}.jpg",  # абсолютный путь
        "instagram":  f"{rel}/cards/instagram/{slug}.jpg",
        "pinterest":  f"{rel}/cards/pinterest/{slug}.jpg",
    }


def cards_exist(md_path: Path, slug: str) -> bool:
    """Проверяет, существуют ли карточки в директории поста."""
    base = md_path.parent / "cards"

    needed = [
        base / "facebook" / f"{slug}.jpg",
        base / "instagram" / f"{slug}.jpg",
        base / "pinterest" / f"{slug}.jpg",
    ]

    return all(path.exists() for path in needed)


def update_front_matter(md_path: Path):
    """Обновляет YAML-шапку Markdown-файла наличием cards: {...}"""
    post = frontmatter.load(md_path)

    slug = post.metadata.get("slug")
    if not slug:
        print(f"[skip] No slug in {md_path}")
        return

    if not cards_exist(md_path, slug):
        print(f"[skip] No cards found for {slug}")
        return

    card_urls = build_card_urls(md_path, slug)

    post.metadata["cards"] = card_urls

    with md_path.open("w", encoding="utf-8") as f:
        frontmatter.dump(post, f)

    print(f"[update] Updated cards for: {slug}")


def main():
    posts = find_posts()
    print(f"[info] Found {len(posts)} posts")

    for md in posts:
        update_front_matter(md)


if __name__ == "__main__":
    main()
