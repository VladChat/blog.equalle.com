# ============================================
# File: scripts/cards/core/text_renderer.py
# Render post titles onto card templates
# ============================================
from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .models import PlatformConfig, Post


MAX_LINES_DEFAULT = 4
FONT_SIZE_RATIO = 0.072
MIN_FONT_SIZE_DEFAULT = 26
TEXT_SHADOW_OFFSET = (2, 2)
TEXT_SHADOW_COLOR = (0, 0, 0, 80)

GRADIENT_TOP = (220, 90, 20)
GRADIENT_BOTTOM = (160, 60, 15)
USE_GRADIENT_TEXT = True

ROUNDED_RADIUS = 40
OUTER_SHADOW_BLUR = 12
OUTER_SHADOW_OFFSET = (5, 5)


def _load_font(font_path: str | None, size: int):
    if font_path:
        fp = Path(font_path)
        if fp.is_file():
            try:
                print(f"[cards][text] Загружаем шрифт {fp} (size={size})")
                return ImageFont.truetype(str(fp), size=size)
            except Exception as e:
                print(f"[cards][text][WARN] Не удалось загрузить шрифт {fp}: {e}")
    print("[cards][text] Используем шрифт по умолчанию Pillow")
    return ImageFont.load_default()


def _text_bbox(draw, text: str, font, spacing: float):
    if not text:
        return (0, 0, 0, 0)
    bbox = draw.multiline_textbbox(
        (0, 0), text, font=font, spacing=spacing, align="center"
    )
    return bbox


def _text_size(draw, text: str, font, spacing: float):
    x0, y0, x1, y1 = _text_bbox(draw, text, font, spacing)
    return (x1 - x0, y1 - y0)


def _wrap_text_to_lines(draw, text: str, font, max_width: int, max_lines: int, spacing: float) -> List[str]:
    words = text.strip().split()
    if not words:
        return []

    lines: List[str] = []
    current_line = ""

    def line_width(candidate: str) -> int:
        w, _ = _text_size(draw, candidate, font, spacing)
        return w

    i = 0
    while i < len(words):
        word = words[i]
        candidate = word if not current_line else current_line + " " + word

        if line_width(candidate) <= max_width:
            current_line = candidate
            i += 1
            continue

        if not current_line and line_width(word) > max_width:
            cut = len(word)
            while cut > 1 and line_width(word[:cut] + "…") > max_width:
                cut -= 1
            if cut <= 1:
                lines.append(word[0] + "…")
            else:
                lines.append(word[:cut] + "…")
            i += 1
        else:
            lines.append(current_line)
            current_line = ""

        if len(lines) == max_lines - 1:
            remaining = " ".join(words[i:])
            if not remaining:
                break
            candidate = remaining
            while candidate and line_width(candidate + "…") > max_width:
                candidate = candidate.rsplit(" ", 1)[0] if " " in candidate else candidate[:-1]
            if not candidate:
                candidate = "…"
            else:
                candidate = candidate + "…"
            lines.append(candidate)
            return lines

    if current_line:
        lines.append(current_line)

    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [lines[max_lines - 1] + "…"]

    return lines[:max_lines]


def _fit_text_to_box(
    base_size, title: str, box_w: int, box_h: int,
    config: PlatformConfig, font_path: str | None,
    max_lines: int = MAX_LINES_DEFAULT, min_font_size: int = MIN_FONT_SIZE_DEFAULT
):
    W, _ = base_size
    start_size = int(W * FONT_SIZE_RATIO)
    if config.font_size:
        start_size = config.font_size

    spacing_factor = config.line_spacing or 1.2

    draw_dummy = ImageDraw.Draw(Image.new("RGBA", (W, box_h), (0, 0, 0, 0)))

    best_font = _load_font(font_path, start_size)
    best_text_block = title
    best_w, best_h = _text_size(draw_dummy, best_text_block, best_font, spacing=0)
    best_size = start_size

    font_size = start_size
    print(f"[cards][text] Подбор шрифта: start_size={start_size}, min_size={min_font_size}, box=({box_w}x{box_h})")

    while font_size >= min_font_size:
        font = _load_font(font_path, font_size)
        spacing = font_size * (spacing_factor - 1.0)

        lines = _wrap_text_to_lines(draw_dummy, title, font, max_width=box_w,
                                    max_lines=max_lines, spacing=spacing)

        text_block = "\n".join(lines)
        tw, th = _text_size(draw_dummy, text_block, font, spacing=spacing)

        print(f"[cards][text]  size={font_size} -> lines={len(lines)}, tw={tw}, th={th}")

        best_font = font
        best_text_block = text_block
        best_w, best_h = tw, th
        best_size = font_size

        if tw <= box_w and th <= box_h:
            print("[cards][text]  -> Влезло в коробку, останавливаемся.")
            break

        font_size -= 1

    print(f"[cards][text] Итоговый размер шрифта={best_size}, text_box=({best_w}x{best_h})")
    return best_font, best_text_block, best_w, best_h, float(best_size)


def _create_vertical_gradient(size, top_color, bottom_color):
    w, h = size
    gradient = Image.new("RGBA", (1, h), (0, 0, 0, 0))

    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top_color[0] + t * (bottom_color[0] - top_color[0]))
        g = int(top_color[1] + t * (bottom_color[1] - top_color[1]))
        b = int(top_color[2] + t * (bottom_color[2] - top_color[2]))
        gradient.putpixel((0, y), (r, g, b, 255))

    return gradient.resize((w, h))


def _draw_gradient_text(base_size, text_block: str, font, position, spacing: float):
    W, H = base_size
    tx, ty = position

    mask = Image.new("L", (W, H), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.multiline_text(
        (tx, ty), text_block, font=font, fill=255,
        spacing=spacing, align="center"
    )

    gradient = _create_vertical_gradient((W, H), GRADIENT_TOP, GRADIENT_BOTTOM)

    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    text_layer.paste(gradient, (0, 0), mask)

    return text_layer


def render_title_on_template(template_path: Path, output_path: Path, post: Post, config: PlatformConfig) -> None:
    print(f"[cards][text] === Рендер карточки для платформы {config.name} ===")
    print(f"[cards][text] Шаблон: {template_path}")
    print(f"[cards][text] Выходной файл: {output_path}")
    print(f"[cards][text] Title: {post.title!r}")

    if not template_path.is_file():
        raise FileNotFoundError(f"Шаблон не найден: {template_path}")

    base = Image.open(str(template_path)).convert("RGBA")
    W, H = base.size

    print(f"[cards][text] Размер шаблона: {W}x{H}")

    if ((config.image_width and config.image_height)
        and ((W, H) != (config.image_width, config.image_height))):
        print(f"[cards][text][WARN] Размер шаблона {template_path.name} = {(W, H)}, "
              f"ожидается {(config.image_width, config.image_height)} для платформы {config.name}")

    title = (post.title or "").strip()
    if not title:
        print("[cards][text][WARN] Пустой title — сохраняем шаблон как есть.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        base.convert("RGB").save(str(output_path), format="JPEG", quality=95)
        return

    x, y, w_box, h_box = config.title_zone
    print(f"[cards][text] title_zone: x={x}, y={y}, w={w_box}, h={h_box}")

    font, text_block, tw, th, used_size = _fit_text_to_box(
        base_size=(W, H),
        title=title,
        box_w=w_box,
        box_h=h_box,
        config=config,
        font_path=config.font_path,
        max_lines=MAX_LINES_DEFAULT,
        min_font_size=MIN_FONT_SIZE_DEFAULT,
    )

    print(f"[cards][text] Итоговый text_block:\n{text_block}")

    x0, y0 = x, y

    # Горизонтальное центрирование
    tx = x0 + (w_box - tw) / 2

    # === Оптическое центрирование текста ===
    OPTICAL_SHIFT = -0.12 * h_box   # поднимаем текст на 12%
    ty = y0 + (h_box - th) / 2 + OPTICAL_SHIFT

    print(f"[cards][text] Оптическое центрирование: shift={OPTICAL_SHIFT}, ty={ty}")

    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)

    spacing = used_size * (config.line_spacing - 1.0)
    sx, sy = TEXT_SHADOW_OFFSET

    tdraw.multiline_text(
        (tx + sx, ty + sy), text_block,
        font=font, fill=TEXT_SHADOW_COLOR,
        spacing=spacing, align="center"
    )

    if USE_GRADIENT_TEXT:
        gradient_layer = _draw_gradient_text(
            base_size=(W, H),
            text_block=text_block,
            font=font,
            position=(tx, ty),
            spacing=spacing,
        )
        text_layer = Image.alpha_composite(text_layer, gradient_layer)
    else:
        tdraw.multiline_text(
            (tx, ty), text_block,
            font=font, fill=(70, 40, 25, 255),
            spacing=spacing, align="center"
        )

    combined = Image.alpha_composite(base, text_layer)

    mask = Image.new("L", (W, H), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (W, H)], radius=ROUNDED_RADIUS, fill=255)

    rounded = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rounded.paste(combined, (0, 0), mask)

    shadow = rounded.filter(ImageFilter.GaussianBlur(OUTER_SHADOW_BLUR))

    out_w = W + OUTER_SHADOW_OFFSET[0]
    out_h = H + OUTER_SHADOW_OFFSET[1]

    bg = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    bg.paste(shadow, OUTER_SHADOW_OFFSET)
    bg.paste(rounded, (0, 0), rounded)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(str(output_path), format="JPEG", quality=95)

    print(f"[cards][text] Карточка сохранена: {output_path}")
