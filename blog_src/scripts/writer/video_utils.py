# ============================================================
# File: blog_src/scripts/writer/video_utils.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\video_utils.py
# ============================================================
"""
video_utils.py — вспомогательные функции для генерации HTML-блока видео
Используется в main_local.py и main.py.
"""

from __future__ import annotations
import html

def build_video_embed(video: dict) -> str:
    """
    Формирует единый HTML-блок:
      - <h2> с названием секции (LLM-переписанный или fallback)
      - краткое описание (blockquote) — если есть
      - iframe YouTube
      - источник
    Подаём сюда СЛОВАРЬ video со следующими ключами:
      - id (обяз.)
      - section_title (опционально) — итоговый заголовок секции
      - video_title_rewritten | title (опционально)
      - video_description | description (опционально)
      - link (опционально)
    """
    if not video or "id" not in video or not video["id"]:
        return ""

    vid = video["id"]
    section = (video.get("section_title") or "Video").strip()
    title = (video.get("video_title_rewritten") or video.get("title") or "").strip()
    desc = (video.get("video_description") or video.get("description") or "").strip()
    source_link = (video.get("link") or f"https://www.youtube.com/watch?v={vid}").strip()

    # Debug
    try:
        print(
            "🔎 [VideoEmbed] section='{section}', title='{title}', desc_present={dp}, "
            "desc_preview='{prev}', source='{src}'".format(
                section=section[:80],
                title=title[:80],
                dp=bool(desc),
                prev=desc[:120],
                src=source_link,
            )
        )
    except Exception as _e:
        print(f"🔎 [VideoEmbed][WARN] Debug print failed: {_e}")

    # Экраним текст
    section_html = html.escape(section) if section else "Video"
    title_html = html.escape(title) if title else "YouTube video"
    desc_html = html.escape(desc) if desc else ""

    parts = []
    parts.append("\n\n<hr/>\n\n")
    parts.append(f"<h2>{section_html}</h2>\n")

    # Описание (если есть)
    if desc_html:
        parts.append(f"<blockquote>{desc_html}</blockquote>\n")

    # Iframe
    parts.append(
        '<div class="video-embed" '
        'style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;">'
    )
    parts.append(
        f'<iframe src="https://www.youtube.com/embed/{vid}" '
        f'title="{title_html}" frameborder="0" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        'allowfullscreen '
        'style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe>'
    )
    parts.append("</div>\n")

    # Источник
    parts.append(
        f'<p style="margin-top:0.5rem;font-size:0.95rem;opacity:0.85;">Video source: '
        f'<a href="{html.escape(source_link)}" target="_blank" rel="noopener nofollow">{title_html}</a></p>\n'
    )

    return "".join(parts)
