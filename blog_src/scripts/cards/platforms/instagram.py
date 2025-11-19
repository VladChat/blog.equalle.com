# ============================================
# File: scripts/cards/platforms/instagram.py
# Instagram card configuration and generator
# ============================================

from __future__ import annotations

from pathlib import Path

from ..core.models import PlatformConfig, Platform, Post
from ..core.text_renderer import render_title_on_template


INSTAGRAM_CONFIG = PlatformConfig(
    name="instagram",
    output_dir="blog_src/content/posts/*/cards/instagram",
    template_dir="blog_src/static/social/templates/ig",
    image_width=1080,
    image_height=1350,
    title_zone=(131, 482, 828, 283),
    font_path="blog_src/static/social/fonts/BungeeSpice-Regular.ttf",
    font_size=72,
    line_spacing=1.2,
)


def instagram_generator(post: Post, template_path: str, output_path: str, config: PlatformConfig) -> None:
    print(f"[cards][instagram] Генерация карточки для поста {post.slug!r}")
    print(f"[cards][instagram] Шаблон: {template_path}")
    print(f"[cards][instagram] Выход: {output_path}")

    render_title_on_template(
        template_path=Path(template_path),
        output_path=Path(output_path),
        post=post,
        config=config,
    )

    print(f"[cards][instagram] Готово: {output_path}")


INSTAGRAM_PLATFORM = Platform(
    config=INSTAGRAM_CONFIG,
    generator=instagram_generator,
)
