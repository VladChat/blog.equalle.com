# ============================================
# File: scripts/cards/core/card_paths.py
# Resolve final card paths and existence
# ============================================

from __future__ import annotations

from pathlib import Path

from .models import PlatformConfig, Post

# Базовая директория контента для постов (Hugo content/)
CONTENT_ROOT = Path("content/posts")


def _get_post_dir(post: Post) -> Path:
    """
    Директория конкретного поста:
    content/posts/<year>/<month>/<day>/<slug>/
    """
    year = post.date.strftime("%Y")
    month = post.date.strftime("%m")
    day = post.date.strftime("%d")
    slug = post.slug

    return CONTENT_ROOT / year / month / day / slug


def _build_card_path(config: PlatformConfig, post: Post, ensure_dirs: bool) -> Path:
    """
    Внутренняя функция, формирующая путь к карточке.

    Итоговый путь:
      content/posts/<year>/<month>/<day>/<slug>/cards/<platform>/<slug>.jpg
    """
    post_dir = _get_post_dir(post)
    platform_name = config.name

    cards_dir = post_dir / "cards" / platform_name
    if ensure_dirs:
        cards_dir.mkdir(parents=True, exist_ok=True)

    output_path = cards_dir / f"{post.slug}.jpg"
    print(f"[cards][paths] [{platform_name}] Итоговый путь карточки: {output_path}")
    return output_path


def get_output_path(config: PlatformConfig, post: Post) -> Path:
    """
    Возвращает путь для сохранения карточки и создаёт нужные директории,
    если их ещё нет.
    """
    return _build_card_path(config, post, ensure_dirs=True)


def card_exists(config: PlatformConfig, post: Post) -> bool:
    """
    Проверяет, существует ли карточка для поста на данной платформе.
    Директории при этом не создаёт.
    """
    path = _build_card_path(config, post, ensure_dirs=False)
    exists = path.is_file()
    if exists:
        print(f"[cards][paths] [{config.name}] Карточка уже существует: {path}")
    else:
        print(f"[cards][paths] [{config.name}] Карточка пока отсутствует: {path}")
    return exists
