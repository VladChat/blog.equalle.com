# ============================================
# File: scripts/cards/platforms/pinterest.py
# Pinterest card configuration and generator
# ============================================

from __future__ import annotations

from pathlib import Path

from ..core.models import PlatformConfig, Platform, Post
from ..core.text_renderer import render_title_on_template


PINTEREST_CONFIG = PlatformConfig(
    name="pinterest",
    output_dir="blog_src/content/posts/*/cards/pinterest",
    template_dir="blog_src/static/social/templates/pn",
    image_width=1000,
    image_height=1500,

    # 🔥 Точно измеренная зона белой плашки под текст
    # (x, y, width, height)
    # Важно: width/height — это ширина и высота, а не правый/нижний край.
    title_zone=(70, 430, 880, 340),

    font_path="blog_src/static/social/fonts/BungeeSpice-Regular.ttf",
    font_size=72,
    line_spacing=1.2,
)


def pinterest_generator(post: Post, template_path: str, output_path: str, config: PlatformConfig) -> None:
    print(f"[cards][pinterest] Генерация карточки для поста {post.slug!r}")
    print(f"[cards][pinterest] Шаблон: {template_path}")
    print(f"[cards][pinterest] Выход: {output_path}")

    render_title_on_template(
        template_path=Path(template_path),
        output_path=Path(output_path),
        post=post,
        config=config,
    )

    print(f"[cards][pinterest] Готово: {output_path}")


PINTEREST_PLATFORM = Platform(
    config=PINTEREST_CONFIG,
    generator=pinterest_generator,
)
