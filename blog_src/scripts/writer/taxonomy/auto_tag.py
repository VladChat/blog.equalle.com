# ============================================================
# File: blog_src/scripts/writer/taxonomy/auto_tag.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\taxonomy\auto_tag.py
# ============================================================

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

# ---------- Paths ----------
DATA_ROOT = Path("blog_src/data")
CATEGORIES_PATH = DATA_ROOT / "categories.json"
TAGS_MASTER_PATH = DATA_ROOT / "tags_master.json"
TAG_STATS_PATH = DATA_ROOT / "tag_stats.json"  # опционально — для «здоровья» тегов

# ---------- Helpers ----------
def _load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s\-/&]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _words(s: str) -> List[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-]+", (s or "").lower())

def _canonize(tag: str, synonyms: Dict[str, str]) -> str:
    t = _normalize(tag)
    return synonyms.get(t, t)

def _whole_word_present(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    # «whole word» для фраз до 3 слов
    esc = re.escape(phrase.lower())
    return re.search(rf"(?<![a-z0-9\-]){esc}(?![a-z0-9\-])", text.lower()) is not None

# ---------- Category picking (новая схема categories.json) ----------
def _iter_categories() -> List[dict]:
    cats = _load_json(CATEGORIES_PATH)
    if isinstance(cats, dict) and "categories" in cats:
        return cats["categories"] or []
    if isinstance(cats, list):
        return cats
    return []

def pick_category(text: str, default: str = "news") -> str:
    """
    Умный выбор категории:
      +3 за совпадение с core-ключами
      +1 за токены из имени категории
      +1 бонус, если встречается slug как отдельное слово
    """
    tnorm = _normalize(text)
    best_name, best_score = None, 0

    for c in _iter_categories():
        name = (c.get("name") or "").strip()
        slug = (c.get("slug") or "").strip()
        kws = c.get("keywords") or {}
        core = kws.get("core") or []
        # core может быть списком строк или словарём -> нормализуем к списку строк
        if isinstance(core, dict):
            core = list(core.keys())
        if not isinstance(core, list):
            core = []

        score = 0
        # Совпадения по core
        for kw in core:
            if _whole_word_present(tnorm, _normalize(kw)):
                score += 3

        # Совпадения по названию категории
        for w in [w for w in _words(name) if len(w) > 2]:
            if re.search(rf"\b{re.escape(w)}\b", tnorm):
                score += 1

        # Бонус за slug
        if slug and re.search(rf"\b{re.escape(slug.lower())}\b", tnorm):
            score += 1

        if score > best_score:
            best_name, best_score = name, score

    return best_name or default

# ---------- Grit extractor ----------
def _find_grit_tags(text: str) -> List[str]:
    """
    Находит P400 / 400 grit / grit 2000 → grit-400 / grit-2000
    """
    res = set()
    low = (text or "").lower()

    for m in re.finditer(r"\b(?:p\s*|grit\s*)(\d{2,4})\b", low):
        n = int(m.group(1))
        if 40 <= n <= 3000:
            res.add(f"grit-{n}")

    for m in re.finditer(r"\b(\d{2,4})\s*grit\b", low):
        n = int(m.group(1))
        if 40 <= n <= 3000:
            res.add(f"grit-{n}")

    return sorted(res, key=lambda x: int(x.split("-")[1]))

# ---------- Headings focus ----------
_HEADING_RE = re.compile(r"(?m)^\s*#{1,6}\s+(.+)$")

def _extract_headings(text: str) -> List[str]:
    return [m.group(1).strip() for m in _HEADING_RE.finditer(text or "")]

# ---------- Tag stats (опционально) ----------
def _load_tag_stats():
    data = _load_json(TAG_STATS_PATH)
    return data if isinstance(data, dict) else {}

def _save_tag_stats(stats: dict):
    _save_json(TAG_STATS_PATH, stats)

def _status_by_site_scale(stats: dict) -> dict:
    total_posts = sum(v.get("count", 0) for v in stats.values()) or 1
    total_tags = max(1, len(stats))
    avg = total_posts / total_tags
    out = {}
    for tag, v in stats.items():
        c = v.get("count", 0)
        if c < 0.5 * avg:
            out[tag] = "rare"
        elif c > 5 * avg:
            out[tag] = "oversaturated"
        elif c > 2 * avg:
            out[tag] = "popular"
        else:
            out[tag] = "normal"
    return out

# ---------- Build tags (строго и «немногословно») ----------
def build_tags(body_text: str, category_name: str, max_tags: int = 8) -> List[str]:
    """
    Принципы:
      1) Начинаем с seed-тегов категории (из tags_master.by_category).
      2) Добавляем grit-теги из текста.
      3) Из канона (tags_master.canonical) берём только то, что реально встречается:
         — приоритет тем, что встречаются в заголовках;
         — затем в первой 1/3 текста;
         — затем по общей частоте (bi/tri-grams).
      4) Фильтруем по чёрному списку, нормализуем по синонимам.
      5) Жёсткий лимит 6–8 тегов. Если мало — добиваем seed-наборами.
      6) Исключаем «редкие» теги (когда сайт уже подрос).
    """
    master = _load_json(TAGS_MASTER_PATH) or {}
    canonical = [ _normalize(t) for t in (master.get("canonical") or []) ]
    blacklist = set( _normalize(t) for t in (master.get("blacklist") or []) )
    synonyms = { _normalize(k): _normalize(v) for k,v in (master.get("synonyms") or {}).items() }
    by_category = { k: [ _normalize(x) for x in v ] for k,v in (master.get("by_category") or {}).items() }

    text_norm = _normalize(body_text)
    headings = " ".join(_extract_headings(body_text)).lower()
    early = body_text[: max(2000, len(body_text)//3) ].lower()

    # 1) Стартовые теги категории
    seeds = list(dict.fromkeys(by_category.get(category_name, [])))  # preserve order & dedup

    # 2) Grit-теги
    grit = _find_grit_tags(body_text)

    # 3) Кандидаты из канона — только те, что реально встречаются
    def score_candidate(tag: str) -> int:
        # высокий вес за наличие в заголовках, средний — в начале, базовый — в тексте
        s = 0
        if _whole_word_present(headings, tag):
            s += 3
        if _whole_word_present(early, tag):
            s += 2
        if _whole_word_present(text_norm, tag):
            s += 1
        return s

    present = []
    for t in canonical:
        if t in blacklist or not t:
            continue
        if not _whole_word_present(text_norm, t):
            continue
        present.append((t, score_candidate(t)))

    # Сортируем по убыванию «важности»
    present.sort(key=lambda x: x[1], reverse=True)

    # 4) Сборка, нормализация и фильтрация
    out: List[str] = []
    seen = set()

    def _push(tag: str):
        tag = _canonize(tag, synonyms)
        if tag in blacklist or not tag or len(tag) < 3 or len(tag) > 40:
            return
        if tag in seen:
            return
        seen.add(tag)
        out.append(tag)

    # — сначала seed-набор
    for t in seeds:
        _push(t)

    # — затем grit-теги (если они в каноне — ок; если нет — всё равно оставляем, это спец-кейс)
    for t in grit:
        if t in blacklist:
            continue
        if t not in seen:
            out.append(t)
            seen.add(t)

    # — затем «важные» из канона
    for t, sc in present:
        if sc <= 0:
            continue
        _push(t)
        if len(out) >= max_tags:
            break

    # Если мало — добиваем из seed-набора (повторная попытка, вдруг что-то фильтровалось)
    if len(out) < 6:
        for t in seeds:
            if t not in seen:
                _push(t)
            if len(out) >= 6:
                break

    # 5) Слишком длинные списки режем жёстко
    out = out[: max(6, min(max_tags, len(out))) ]

    # 6) Статистика + фильтр «редких», но только когда контента накопилось
    stats = _load_tag_stats()
    for t in out:
        stats.setdefault(t, {"count": 0})
        stats[t]["count"] += 1
    _save_tag_stats(stats)

    status = _status_by_site_scale(stats)
    if sum(v["count"] for v in stats.values()) > 20:
        filtered = [t for t in out if status.get(t, "normal") not in ("rare",)]
        if len(filtered) >= 6:
            out = filtered[: max(6, min(max_tags, len(filtered))) ]

    return out
