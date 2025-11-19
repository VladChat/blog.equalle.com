# ============================================
# File: scripts/cards/core/card_paths.py
# Resolve final card paths and existence
# ============================================

from __future__ import annotations

from pathlib import Path

from .models import PlatformConfig, Post


def get_output_path(config: PlatformConfig, post: Post) -> Path:
    """Формирует путь:
       blog_src/content/posts/<year>/<month>/cards/<platform>/<slug>.jpg
    """
    md_path = post.source_path
    month_dir = md_path.parent
    platform_name = config.name

    cards_dir = month_dir / "cards" / platform_name
    output_path = cards_dir / f"{post.slug}.jpg"

    print(f"[cards][paths] [{platform_name}] Итоговый путь карточки: {output_path}")
    return output_path


def card_exists(config: PlatformConfig, post: Post) -> bool:
    """Проверяет, существует ли карточка для поста на данной платформе."""
    path = get_output_path(config, post)
    exists = path.is_file()
    if exists:
        print(f"[cards][paths] [{config.name}] Карточка уже существует: {path}")
    else:
        print(f"[cards][paths] [{config.name}] Карточка пока отсутствует: {path}")
    return exists
