# ============================================
# File: scripts/cards/platforms/facebook.py
# Facebook card configuration and generator
# ============================================

from __future__ import annotations

from pathlib import Path

from ..core.models import PlatformConfig, Platform, Post
from ..core.text_renderer import render_title_on_template


FACEBOOK_CONFIG = PlatformConfig(
    name="facebook",
    output_dir="blog_src/content/posts/*/cards/facebook",
    template_dir="blog_src/static/social/templates/fb",
    image_width=1500,
    image_height=1500,

    # 🔥 Исправленная зона под текст внутри белой плашки
    # (x, y, width, height)
    # Важно: width — это ширина, а не правая координата.
    title_zone=(350, 470, 800, 270),

    font_path="blog_src/static/social/fonts/BungeeSpice-Regular.ttf",
    font_size=64,
    line_spacing=1.2,
)


def facebook_generator(post: Post, template_path: str, output_path: str, config: PlatformConfig) -> None:
    print(f"[cards][facebook] Генерация карточки для поста {post.slug!r}")
    print(f"[cards][facebook] Шаблон: {template_path}")
    print(f"[cards][facebook] Выход: {output_path}")

    render_title_on_template(
        template_path=Path(template_path),
        output_path=Path(output_path),
        post=post,
        config=config,
    )

    print(f"[cards][facebook] Готово: {output_path}")


FACEBOOK_PLATFORM = Platform(
    config=FACEBOOK_CONFIG,
    generator=facebook_generator,
)
