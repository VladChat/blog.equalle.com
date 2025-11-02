# ============================================================
# File: blog_src/scripts/writer/prompt_builder.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\prompt_builder.py
# ============================================================

import re
from pathlib import Path
from typing import Optional, Dict


class _SafeDict(dict):
    """format_map-safe dict: missing keys resolve to empty strings, not KeyError."""
    def __missing__(self, key):
        return ""


def _resolve_template_path() -> Optional[Path]:
    """
    Ищет prompt_template.txt в нескольких предсказуемых местах.
    Возвращает первый существующий путь или None.
    """
    here = Path(__file__).resolve()
    # this file: blog_src/scripts/writer/prompt_builder.py
    # go up to blog_src
    blog_src = here.parents[2]

    candidates = [
        blog_src / "config" / "prompt_template.txt",           # ✅ preferred (repo layout)
        Path.cwd() / "blog_src" / "config" / "prompt_template.txt",  # CWD-based
        Path("blog_src/config/prompt_template.txt"),           # relative fallback
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_prompt_template() -> str:
    """
    Загружает текст шаблона промпта. Если файл не найден — возвращает минимальный fallback.
    """
    p = _resolve_template_path()
    if p is None:
        # Fallback: минимальный «универсальный» шаблон
        fallback = (
            "{style_hint}\n\n"
            "# {topic}\n\n"
            "{summary}\n"
            "{original_url}\n"
            "{video_info}\n"
            "{main_kw}\n"
        )
        try:
            print("───────────────────────────────")
            print("🔍 [PromptBuilder] Diagnostics")
            print("  - template path: NOT FOUND (using fallback inline template)")
            print("───────────────────────────────")
        except Exception:
            pass
        return fallback

    try:
        txt = p.read_text(encoding="utf-8")
        try:
            print("───────────────────────────────")
            print("🔍 [PromptBuilder] Diagnostics")
            print(f"  - template path: {p}")
            print("───────────────────────────────")
        except Exception:
            pass
        return txt
    except Exception as e:
        # Если вдруг не удалось прочитать — вернём fallback
        try:
            print("───────────────────────────────")
            print("🔍 [PromptBuilder] Diagnostics")
            print(f"  - template path: {p} (read FAIL: {e})")
            print("  - using fallback inline template")
            print("───────────────────────────────")
        except Exception:
            pass
        return (
            "{style_hint}\n\n"
            "# {topic}\n\n"
            "{summary}\n"
            "{original_url}\n"
            "{video_info}\n"
            "{main_kw}\n"
        )


def _build_video_info_field(video: Optional[Dict] = None, video_info: str = "") -> str:
    """
    Возвращает строку для {video_info} в шаблоне.
    Приоритет: явный video_info (строка) > разобранный словарь video > "None".
    """
    # 1) Явная строка из аргумента
    if isinstance(video_info, str) and video_info.strip():
        return video_info.strip()

    # 2) Словарь video (старый/расширенный путь)
    if isinstance(video, dict):
        v_title = (video.get("title") or "").strip()
        v_url = (video.get("link") or "").strip()
        v_publ = (video.get("published") or "").strip()
        v_desc_raw = (video.get("video_description") or "")

        # sanitize description
        v_desc_clean = re.sub(r"<[^>]+>", "", v_desc_raw)
        v_desc_clean = re.sub(r"\s+", " ", v_desc_clean).strip().lower()

        placeholder_phrases = {
            "watch this short overview video",
            "watch this video",
            "short overview video",
            "no description",
            "n/a",
            "na",
            "tbd",
            "coming soon",
        }

        is_placeholder = (
            not v_desc_clean
            or len(v_desc_clean.split()) < 5
            or any(p in v_desc_clean for p in placeholder_phrases)
        )

        if is_placeholder:
            v_desc_for_prompt = (
                f"Write 2–3 natural sentences describing the YouTube video titled "
                f"'{v_title}'. Explain what it covers and why it matters in the "
                f"context of this article. Do not copy from the title; paraphrase."
            )
        else:
            v_desc_for_prompt = (v_desc_raw or "").strip()

        return (
            "Title: " + v_title + "\n"
            "Summary: " + v_desc_for_prompt + "\n"
            "URL: " + v_url + "\n"
            "Published: " + v_publ
        )

    # 3) Ничего нет — вернём "None"
    return "None"


def build_prompt(
    topic: str,
    summary: str,
    original_url: Optional[str] = None,
    video: Optional[Dict] = None,
    style_hint: str = "",
    main_kw: str = "",
    video_info: str = "",   # ✅ новый необязательный параметр для совместимости с main_local.py
) -> str:
    """
    Forms the final prompt string by loading a template and injecting fields.

    - Совместимость:
      * Поддерживает как старый путь (video: dict), так и новый (video_info: str).
      * Безопасно обрабатывает отсутствие плейсхолдеров в шаблоне.
      * Любые отсутствующие ключи не ломают форматирование (см. _SafeDict).

    - Диагностика:
      * Печатает детальные логи о наличии плейсхолдеров и о режиме сборки (STANDARD/COLLAPSED).
    """
    template = load_prompt_template()

    has_topic = "{topic}" in template
    has_summary = "{summary}" in template
    has_original = "{original_url}" in template
    has_video = "{video_info}" in template
    has_main_kw = "{main_kw}" in template
    has_style = "{style_hint}" in template

    topic_field = (topic or "").strip()
    summary_field = (summary or "").strip()
    original_field = (original_url or "").strip()
    style_field = (style_hint or "").strip()
    mainkw_field = (main_kw or "").strip()

    # Собираем видео-поле с приоритетом явной строки
    video_info_field = _build_video_info_field(video=video, video_info=video_info)

    # --- Diagnostics (non-fatal) ---
    try:
        print("───────────────────────────────")
        print("🔍 [PromptBuilder] Diagnostics")
        print("  - template placeholders:")
        print(f"      {{topic}}:       {has_topic}")
        print(f"      {{summary}}:     {has_summary}")
        print(f"      {{original_url}}:{has_original}")
        print(f"      {{video_info}}:  {has_video}")
        print(f"      {{main_kw}}:     {has_main_kw}")
        print(f"      {{style_hint}}:  {has_style}")
        print("  - values (trimmed):")
        print(f"      topic:        {topic_field[:80] + ('…' if len(topic_field) > 80 else '')}")
        print(f"      summary.len:  {len(summary_field)}")
        print(f"      original_url: {original_field if original_field else 'N/A'}")
        print(f"      main_kw:      {mainkw_field if mainkw_field else 'N/A'}")
        print(f"      video_info:   {'provided' if video_info_field and video_info_field != 'None' else 'None'}")
        print("───────────────────────────────")
    except Exception:
        # Logging must never break prompt building
        pass

    # Если шаблон НЕ содержит ни summary/original/video (часто кастомные минимал-шаблоны),
    # коллапсируем всё в {topic}, но оставляем возможность прокинуть style_hint/main_kw.
    if not (has_summary or has_original or has_video):
        try:
            print("🔧 [PromptBuilder] Mode: COLLAPSED (no summary/original/video placeholders)")
        except Exception:
            pass
        topic_block = topic_field
        if original_field:
            topic_block += f"\n\nOriginal source: {original_field}"
        if summary_field:
            topic_block += f"\n\nContext: {summary_field}"
        else:
            topic_block += "\n\nContext: "

        return template.format_map(
            _SafeDict(
                {
                    "topic": topic_block,
                    "style_hint": style_field,
                    "main_kw": mainkw_field,
                }
            )
        )

    # Стандартный путь: заполняем все возможные плейсхолдеры, недостающие будут пустыми.
    try:
        print("🔧 [PromptBuilder] Mode: STANDARD (placeholders present)")
    except Exception:
        pass

    return template.format_map(
        _SafeDict(
            {
                "topic": topic_field,
                "summary": summary_field,
                "original_url": original_field,
                "video_info": video_info_field,
                "style_hint": style_field,
                "main_kw": mainkw_field,
            }
        )
    )
