# ============================================================
# File: blog_src/scripts/writer/link_injector.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\link_injector.py
# ============================================================

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

# === CONFIG ===
DATA_DIR = Path("blog_src/data")
STATE_FILE = DATA_DIR / "state.json"
AMAZON_PATH = DATA_DIR / "internal_links_amazon.json"
EQUALLE_PATH = DATA_DIR / "internal_links_equalle.json"

# Preferred pack rotation (kept here to avoid magic numbers)
PACK_ROTATION: List[int] = [25, 50, 100]


# === STATE HELPERS ===
def _load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# === CORE LOADER ===
def load_links():
    """Поочередно загружает internal_links_amazon.json и internal_links_equalle.json."""
    state = _load_state()
    last = state.get("last_source", "amazon")
    source = "equalle" if last == "amazon" else "amazon"
    state["last_source"] = source
    _save_state(state)

    path = EQUALLE_PATH if source == "equalle" else AMAZON_PATH
    print(f"🔗 Loaded {source.upper()} links ({path.name})")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# === CONTEXT → GRIT MAPPER (NEW) ===
def _preferred_grits_for_context(context: str, meta: Dict) -> List[int]:
    """
    Возвращает приоритетный список гритов на основе текстового контекста.
    Если ничего не найдено — пытается взять из meta.context_map[context],
    затем — из meta.grit_clusters (любой грит как запасной вариант).
    """
    ctx = (context or "").lower()
    # 1) Жёсткие правила по фразам в контенте
    # "before primer" → 150–240 и 320 как верхняя ступень подготовки
    if "before primer" in ctx or "pre-primer" in ctx:
        return [150, 180, 220, 240, 320]

    # "between coats" → межслойная зачистка
    if "between coat" in ctx or "between-coat" in ctx:
        return [320, 400, 600]

    # "finish/polish/headlight/mirror/swirl" → финиш/полировка
    if any(kw in ctx for kw in ("final", "finish", "polish", "swirl", "headlight", "mirror")):
        return [800, 1000, 1500, 2000]

    # auto body generic
    if any(kw in ctx for kw in ("auto body", "auto-body", "auto paint", "auto sanding")):
        return [80, 120, 150, 180, 220, 240]

    # 2) Попытка взять из meta.context_map
    ctx_map = (meta or {}).get("context_map", {})
    mapped = ctx_map.get(context, [])
    if mapped:
        return mapped

    # 3) Фоллбек: любой грит из кластеров (берём один наиболее «средний»)
    grit_clusters = (meta or {}).get("grit_clusters", {})
    if grit_clusters:
        flat = []
        for arr in grit_clusters.values():
            flat.extend(arr)
        # Дедуп и сортировка по «близости к 220» как более универсальному
        flat = sorted(set(flat), key=lambda g: abs(int(g) - 220))
        return flat

    return []


# === PRODUCT PICKER ===
def pick_product_link(context: str, links: dict) -> dict:
    """
    Выбирает одну ссылку по контексту, соблюдая приоритет гритов/паков и исключая повторы,
    пока не пройдет круг. Сохраняет текущую логику данных links (products/meta).
    """
    meta = links.get("meta", {})
    # Получаем приоритетные грипы с учётом контекста (НОВАЯ логика)
    grit_options: List[int] = _preferred_grits_for_context(context, meta)

    # === РОТАЦИЯ БЕЗ ПОВТОРОВ ===
    state = _load_state()
    used_links = set(state.get("used_links", []))

    # Собираем все возможные комбинации pack+grit
    # Ожидаем структуру:
    # "products": {
    #   "25_pack": { "Grit 180": "url", "Grit 220": "url", ... },
    #   "50_pack": { ... },
    #   "100_pack": { ... }
    # }
    all_combos: List[Tuple[str, str, str, str]] = []
    for pack_key, grits in links.get("products", {}).items():
        for grit, url in grits.items():
            combo = f"{pack_key}_{grit}"
            all_combos.append((pack_key, grit, url, combo))

    # Helper: извлечь числовой грит и размер пака
    def _grit_id(grit_label: str) -> int:
        # Берём последний токен, должен быть число (например, "Grit 220" → "220")
        try:
            return int(grit_label.split()[-1])
        except Exception:
            return -1

    def _pack_num(pack_key: str) -> int:
        # "25_pack" → 25
        try:
            return int(pack_key.split("_")[0])
        except Exception:
            return 999

    # Фильтруем по контексту (если есть приоритетный список)
    if grit_options:
        allowed_grits = set(map(int, grit_options))
        context_combos = [
            (p, g, u, c)
            for (p, g, u, c) in all_combos
            if _grit_id(g) in allowed_grits
        ]
    else:
        context_combos = []

    candidate_space = context_combos or all_combos

    # Исключаем уже использованные
    available = [item for item in candidate_space if item[3] not in used_links]

    # Если всё уже использовано — начинаем новый круг
    if not available:
        used_links = set()
        available = candidate_space

        # Если по какой-то причине и он пуст — вернёмся к all_combos
        if not available:
            available = all_combos

    # NEW: вместо random — детерминированная сортировка по приоритету
    # 1) Позиция грида в grit_options (если не найден — большой индекс)
    # 2) Позиция пака в PACK_ROTATION (25→50→100)
    # 3) Стабильный tie-breaker — по алфавиту combo (чтобы не прыгало)
    def _priority(item: Tuple[str, str, str, str]) -> Tuple[int, int, str]:
        p_key, g_label, _url, combo = item
        g_num = _grit_id(g_label)

        if grit_options:
            try:
                g_idx = grit_options.index(g_num)
            except ValueError:
                g_idx = 999
        else:
            # Если приоритет не задан — центрируем вокруг 220
            g_idx = abs(g_num - 220)

        p_num = _pack_num(p_key)
        try:
            p_idx = PACK_ROTATION.index(p_num)
        except ValueError:
            p_idx = 99

        return (g_idx, p_idx, combo)

    available.sort(key=_priority)
    pack_key, grit, url, combo = available[0]

    # Регистрируем использование
    used_links.add(combo)
    state["used_links"] = list(used_links)
    _save_state(state)

    # Получаем описание (если есть)
    grit_id_str = str(_grit_id(grit))
    info = meta.get("grit_copy", {}).get(grit_id_str, {})

    return {
        "url": url,
        "grit": grit_id_str,
        "pack": int(pack_key.split("_")[0]),
        "anchor": info.get("anchor", f"{grit_id_str} Grit"),
        "desc": info.get("desc", "")
    }


# === HTML BUILDER ===
def build_link_html(product: dict) -> str:
    """Создает HTML блок: короткая ссылка + расширенное описание"""
    if not product:
        return ""

    url = product["url"]
    anchor = product["anchor"]
    desc = product["desc"]
    pack = product["pack"]

    SIZE = "9x11 in"
    MATERIAL = "Silicon Carbide Abrasive"
    USAGE = "Wet or Dry Use"
    GRADE = "Professional Grade"

    base_anchor = anchor.split(" (", 1)[0]
    link_title = f"{base_anchor} Sandpaper Sheets ({pack}-pack)"
    extended_desc = f"{SIZE} {MATERIAL} for {USAGE} — {desc} ({GRADE})."

    return (
        f'<div class="equalle-product-link">'
        f'<p><a href="{url}" target="_blank">{link_title}</a> — {extended_desc}</p>'
        f'</div>'
    )


# === MAIN INJECTOR ===
def inject_product_link_after_video_source(body_html: str, context: str) -> str:
    """Вставляет ссылку сразу после блока 'Video source:' или в конец статьи."""
    links = load_links()
    product = pick_product_link(context, links)
    snippet = build_link_html(product)

    if not snippet:
        return body_html

    marker = body_html.find("Video source:")
    if marker != -1:
        end_tag = body_html.find("</p>", marker)
        if end_tag != -1:
            return body_html[:end_tag + 4] + snippet + body_html[end_tag + 4:]

    return body_html + snippet


# === FALLBACK ===
def inject_product_link_first_section(body_html: str, context: str) -> str:
    """Вставляет ссылку после первого смыслового блока (<h3> или <ol>)."""
    links = load_links()
    product = pick_product_link(context, links)
    snippet = build_link_html(product)

    if not snippet:
        return body_html

    insertion_point = body_html.find("</h3>")
    if insertion_point == -1:
        insertion_point = body_html.find("</ol>")
    if insertion_point != -1:
        body_html = body_html[:insertion_point + 5] + snippet + body_html[insertion_point + 5:]
    else:
        body_html += snippet
    return body_html
