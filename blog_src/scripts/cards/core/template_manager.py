# ============================================
# File: scripts/cards/core/template_manager.py
# Template discovery and rotation per platform
# ============================================

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import PlatformConfig

TEMPLATE_STATE_PATH = Path("blog_src/data/social_template_state.json")


def _load_state() -> dict:
    if not TEMPLATE_STATE_PATH.exists():
        print(f"[cards][templates] Файл состояния не найден, начинаем с пустого: {TEMPLATE_STATE_PATH}")
        return {}
    try:
        state = json.loads(TEMPLATE_STATE_PATH.read_text(encoding="utf-8"))
        print(f"[cards][templates] Загружено состояние шаблонов: {state}")
        return state
    except Exception as e:
        print(f"[cards][templates][ERROR] Не удалось прочитать {TEMPLATE_STATE_PATH}: {e}")
        return {}


def _save_state(state: dict) -> None:
    TEMPLATE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"[cards][templates] Сохранено новое состояние шаблонов: {state}")


def _list_template_files(config: PlatformConfig) -> List[Path]:
    template_dir = Path(config.template_dir)
    if not template_dir.exists():
        print(f"[cards][templates][ERROR] Директория шаблонов не найдена: {template_dir}")
        return []

    files = sorted(template_dir.glob("*.jpg"))
    print(f"[cards][templates] [{config.name}] Найдено {len(files)} шаблон(ов) в {template_dir}")
    return files


def get_next_template(config: PlatformConfig) -> Path:
    state = _load_state()
    platform_name = config.name

    templates = _list_template_files(config)
    if not templates:
        raise RuntimeError(f"Не найдены шаблоны для платформы {platform_name} в {config.template_dir}")

    idx = state.get(platform_name, 0)
    template_path = templates[idx % len(templates)]

    print(f"[cards][templates] [{platform_name}] Используем шаблон #{idx} -> {template_path.name}")

    state[platform_name] = (idx + 1) % len(templates)
    _save_state(state)

    return template_path
