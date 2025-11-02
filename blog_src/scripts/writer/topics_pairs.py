# ============================================================
# File: blog_src/scripts/writer/topics_pairs.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topics_pairs.py
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────

_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parents[3]  # ...\blog.equalle.com
_DATA_DIR = _PROJECT_ROOT / "blog_src" / "data"
_CATEGORIES_JSON = _DATA_DIR / "categories.json"
_STATE_JSON = _DATA_DIR / "state.json"

# ────────────────────────────────────────────────────────────
# Model
# ────────────────────────────────────────────────────────────

@dataclass
class CategoryLite:
    name: str
    slug: str

# ────────────────────────────────────────────────────────────
# IO helpers
# ────────────────────────────────────────────────────────────

def _safe_read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[eQualle PAIR][ERR] ⚠️ Failed to read JSON: {path} — {e}")
        return {}

def _safe_write_json(path: Path, obj: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[eQualle PAIR][ERR] ⚠️ Failed to write JSON: {path} — {e}")

# ────────────────────────────────────────────────────────────
# Loaders
# ────────────────────────────────────────────────────────────

def _load_categories(categories_path: Path) -> Tuple[List[CategoryLite], Dict[str, Dict[str, Any]]]:
    """
    Поддерживает фактическую схему:
      keywords.core = { "<core seed>": [ "<longtail1>", "<longtail2>", ... ], ... }
    Возвращает:
      - список категорий (name, slug)
      - kw_map: { slug: { "cores": [seed...], "longs_by_core": {seed: [lt...]} } }
    """
    raw = _safe_read_json(categories_path)
    arr = raw.get("categories", []) if isinstance(raw, dict) else []
    categories: List[CategoryLite] = []
    kw_map: Dict[str, Dict[str, Any]] = {}

    for item in arr:
        name = (item.get("name") or "").strip()
        slug = (item.get("slug") or "").strip()
        if not name or not slug:
            continue
        categories.append(CategoryLite(name=name, slug=slug))

        kw = item.get("keywords") or {}
        core_obj = kw.get("core") or {}
        cores: List[str] = []
        longs_by_core: Dict[str, List[str]] = {}

        # Ожидаемый новый формат: core — dict
        if isinstance(core_obj, dict):
            cores = list(core_obj.keys())  # порядок сохраняется как в JSON
            for seed, lt_list in core_obj.items():
                if isinstance(lt_list, list):
                    longs_by_core[seed] = [str(x).strip() for x in lt_list if str(x).strip()]
                else:
                    longs_by_core[seed] = []
        # На всякий случай fallback (старые форматы)
        elif isinstance(core_obj, list):
            cores = [str(x).strip() for x in core_obj if str(x).strip()]
            longs_by_core = {seed: [] for seed in cores}
        else:
            cores = []
            longs_by_core = {}

        if not cores:
            # Если совсем пусто — используем имя категории как единственный core
            cores = [name]
            longs_by_core[name] = []

        kw_map[slug] = {"cores": cores, "longs_by_core": longs_by_core}

    print(f"[eQualle PAIR][CATS][LOAD] 📚 categories={len(categories)} from {categories_path}")
    return categories, kw_map


def _load_state(state_path: Path) -> Dict[str, Any]:
    st = _safe_read_json(state_path)
    if not isinstance(st, dict):
        st = {}
    st.setdefault("category_index", 0)
    st.setdefault("per_category", {})
    return st


def _save_state(state_path: Path, st: Dict[str, Any]) -> None:
    _safe_write_json(state_path, st)
    print(f"[eQualle PAIR][STATE][OK] 💾 Saved state → {state_path}")

# ────────────────────────────────────────────────────────────
# Core selection logic
# ────────────────────────────────────────────────────────────

def _bucket_for_category(st: Dict[str, Any], slug: str) -> Dict[str, int]:
    per = st.setdefault("per_category", {})
    bucket = per.setdefault(slug, {})
    bucket.setdefault("core_idx", 0)
    bucket.setdefault("longtail_idx", 0)
    return bucket


def _select_for_category(cat: CategoryLite, kw_map: Dict[str, Dict[str, Any]], st: Dict[str, Any]) -> Tuple[str, str]:
    """
    Правила (по твоей логике):
      1) Идём по всем core по кругу, при этом используем один и тот же номер longtail_idx.
      2) Когда круг core завершился → сбрасываем core_idx=0, увеличиваем longtail_idx += 1.
      3) Для каждого core longtail берётся из его собственного списка (по индексу lt_idx % len(list)).
         Если списка нет/пуст — fallback на сам core.
    """
    bucket = _bucket_for_category(st, cat.slug)
    core_idx = int(bucket.get("core_idx", 0))
    lt_idx = int(bucket.get("longtail_idx", 0))

    cores = (kw_map.get(cat.slug) or {}).get("cores", []) or [cat.name]
    longs_by_core = (kw_map.get(cat.slug) or {}).get("longs_by_core", {}) or {}

    # Нормализация индексов
    core_idx_norm = core_idx % len(cores)
    core_seed = cores[core_idx_norm]
    lt_list = longs_by_core.get(core_seed, []) or []

    if lt_list:
        longtail = lt_list[lt_idx % len(lt_list)]
    else:
        longtail = core_seed  # fallback

    # ЛОГИ подробные
    print(f"[eQualle PAIR][SELECT] 🧩 Category={cat.name} ({cat.slug})")
    print(f"[eQualle PAIR][SELECT]    core_idx={core_idx_norm}/{len(cores)-1}, longtail_idx={lt_idx}")
    if lt_list:
        print(f"[eQualle PAIR][SELECT]    core='{core_seed}' → longtails[{len(lt_list)}], using idx={lt_idx % len(lt_list)}")
    else:
        print(f"[eQualle PAIR][SELECT]    core='{core_seed}' → no longtails → fallback to core")
    print(f"[eQualle PAIR][SELECT]    -> seed='{core_seed}' + longtail='{longtail}'")

    # Продвижение индексов на следующий вызов
    core_idx_next = (core_idx_norm + 1) % len(cores)
    if core_idx_next == 0:
        lt_idx_next = lt_idx + 1
    else:
        lt_idx_next = lt_idx

    bucket["core_idx"] = core_idx_next
    bucket["longtail_idx"] = lt_idx_next
    st["per_category"][cat.slug] = bucket

    return core_seed, longtail


def get_next_pair(categories_path: Path, state_path: Path) -> Tuple[CategoryLite, str, str]:
    """
    Главная точка входа для main_local.py:
      - крутит категории по кругу (глобально),
      - выбирает seed/longtail по правилам внутри категории,
      - сохраняет обновлённый state.
    """
    cats, kw_map = _load_categories(categories_path)
    st = _load_state(state_path)

    if not cats:
        raise RuntimeError("No categories loaded. Check categories.json")

    cidx = int(st.get("category_index", 0)) % len(cats)
    cat = cats[cidx]

    print(f"[eQualle PAIR][STATE][LOAD] 🔁 category_index={st.get('category_index', 0)}")
    seed, longtail = _select_for_category(cat, kw_map, st)

    # Глобальная ротация категорий
    st["category_index"] = (cidx + 1) % len(cats)
    _save_state(state_path, st)

    return cat, seed, longtail


def record_used_pair(state_path: Path, seed: str, longtail: str) -> None:
    """
    Совместимость с существующими вызовами: просто фиксируем факт использования пары.
    """
    st = _load_state(state_path)
    used = st.setdefault("used_pairs", [])
    used.append({"seed": seed, "longtail": longtail})
    _save_state(state_path, st)
    print(f"[eQualle PAIR][STATE] 📝 Recorded used pair: seed='{seed}' | longtail='{longtail}'")
