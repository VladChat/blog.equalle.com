# ============================================================
# File: blog_src/scripts/writer/video_helpers.py
# ============================================================
"""
video_helpers.py — утилиты для работы с "Видео"-секцией в Markdown.
Задачи:
  • Сделать безопасный заголовок секции для видео.
  • Извлечь краткое описание видео, если LLM сгенерировал текст под заголовком "Video".
  • Удалить любую LLM-созданную секцию "Video" (во избежание дублирования).
"""

from __future__ import annotations

import re
from typing import Optional


def _make_section_title(src_title: str) -> str:
    """
    Делаем лаконичное название секции на основе заголовка ролика.
    Пример: "Video: How to Sand Walnut Without Swirls"
    """
    t = (src_title or "").strip()
    t = re.sub(r"\s+", " ", t)
    # Усечение очень длинных заголовков
    if len(t) > 90:
        t = t[:87].rstrip() + "…"
    return f"Video: {t}" if t else "Video"


def _extract_video_description_from_md(md: str, video: Optional[dict] = None) -> str:
    """
    Ищем краткое описание под заголовком "Video" (любой уровень #).
    Берем один абзац (до пустой строки/следующего заголовка).

    Совместимость со старым вызовом:
    - теперь функция принимает второй параметр `video`, но он опционален и может не использоваться.
    """
    if not md:
        return ""

    # Заголовок "Video" любым уровнем (##, ###, #### и т.п.), с любым хвостом после "Video"
    h_re = re.compile(r"(?mi)^\s*#{1,6}\s*video\b[^\n]*\n+")
    m = h_re.search(md)
    if not m:
        return ""

    rest = md[m.end():]

    # До следующего заголовка или конца
    stop = re.search(r"(?mi)^\s*#{1,6}\s+\S", rest)
    chunk = rest[: stop.start() if stop else len(rest)]

    # Берем первый непустой абзац/blockquote
    # Сначала пробуем blockquote
    qb = re.search(r"(?s)^\s*>\s*(.+?)(?:\n\s*\n|$)", chunk)
    if qb:
        return qb.group(1).strip()

    # Иначе обычный абзац
    pb = re.search(r"(?s)^\s*(.+?)(?:\n\s*\n|$)", chunk)
    return pb.group(1).strip() if pb else ""


def _strip_llm_video_section(md: str, video: Optional[dict]) -> str:
    """
    Удаляем любую LLM-созданную секцию Video, чтобы не было дублей.
    1) Любой заголовок уровня 1–6, начинающийся со слова "Video".
    2) Если есть video['section_title'], удаляем и такой заголовок.
    """
    if not md:
        return md

    # 1) Любой "Video..." на H1–H6
    pat1 = re.compile(r"(?mis)^\s*#{1,6}\s*video\b[^\n]*\n.*?(?=^\s*#{1,6}\s+\S|\Z)")
    md2 = re.sub(pat1, "", md)

    # 2) Конкретный секционный заголовок (на всякий случай)
    section_title = (video or {}).get("section_title", "")
    if section_title:
        esc = re.escape(section_title)
        pat2 = re.compile(rf"(?mis)^\s*#{1,6}\s*{esc}\s*\n.*?(?=^\s*#{1,6}\s+\S|\Z)")
        md2 = re.sub(pat2, "", md2)

    # Чистим возможные лишние пустые строки
    md2 = re.sub(r"\n{3,}", "\n\n", md2).strip() + "\n"
    return md2
