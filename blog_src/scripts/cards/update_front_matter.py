# ============================================
# File: blog_src/scripts/cards/update_front_matter.py
# Purpose: Inject social card URLs into Markdown front matter
# ============================================

from __future__ import annotations

import frontmatter
from pathlib import Path

# Базовая директория контента для постов (Hugo content/)
CONTENT_ROOT = Path("content/posts")


def find_posts() -> list[Path]:
    """Находит все index.md во всех постовых директориях."""
    return list(CONTENT_ROOT.rglob("index.md"))


def build_card_urls(post_dir: Path, slug: str) -> dict:
    """
    Строит словарь URL карточек для front matter:

    cards:
      facebook:  /posts/.../cards/facebook/slug.jpg
      twitter:   /posts/.../cards/facebook/slug.jpg
      instagram: /posts/.../cards/instagram/slug.jpg
      pinterest: /posts/.../cards/pinterest/slug.jpg
    """

    # Путь вида /posts/YYYY/MM/DD/slug
    # content/ убираем, оставляя только сайт-путь
    rel_post_path = "/" + str(post_dir.relative_to("content")).replace("\\", "/")

    cards = {
        "facebook":  f"{rel_post_path}/cards/facebook/{slug}.jpg",
        "twitter":   f"{rel_post_path}/cards/facebook/{slug}.jpg",  # twitter = facebook
        "instagram": f"{rel_post_path}/cards/instagram/{slug}.jpg",
        "pinterest": f"{rel_post_path}/cards/pinterest/{slug}.jpg",
    }

    return cards


def cards_exist(post_dir: Path, slug: str) -> bool:
    """Проверяет, существуют ли карточки в директории поста."""
    base = post_dir / "cards"

    needed = [
        base / "facebook" / f"{slug}.jpg",
        base / "instagram" / f"{slug}.jpg",
        base / "pinterest" / f"{slug}.jpg",
    ]

    return all(path.exists() for path in needed)


def update_front_matter(md_path: Path) -> None:
    """Обновляет YAML-шапку Markdown-файла наличием cards: {...}."""
    post_dir = md_path.parent

    # Загружаем markdown
    post = frontmatter.load(md_path)

    slug = post.metadata.get("slug")
    if not slug:
        print(f"[skip] No slug in {md_path}")
        return

    # Проверяем, есть ли карточки
    if not cards_exist(post_dir, slug):
        print(f"[skip] No cards found for {slug}")
        return

    # Создаём словарь URL
    card_urls = build_card_urls(post_dir, slug)

    # Прописываем в YAML
    post.metadata["cards"] = card_urls

    # Сохраняем файл обратно
    with md_path.open("w", encoding="utf-8") as f:
        frontmatter.dump(post, f)

    print(f"[update] Updated cards for: {slug}")


def main() -> None:
    posts = find_posts()
    print(f"[info] Found {len(posts)} posts")

    for md in posts:
        update_front_matter(md)


if __name__ == "__main__":
    main()
