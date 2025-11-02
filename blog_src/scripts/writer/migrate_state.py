# ============================================================
# File: blog_src/scripts/writer/migrate_state.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\migrate_state.py
# ============================================================
from __future__ import annotations

import json
from pathlib import Path


def migrate_state(state_path: Path) -> None:
    if not state_path.exists():
        state = {
            "rotation": {"cat_i": 0, "seed_i": 0, "lt_i": 0},
            "used_pairs": [],
            "seen": [],
            "used_links": [],
            "last_video_ids": []
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"[migrate_state] ✅ Created new state at: {state_path}")
        return

    with state_path.open("r", encoding="utf-8") as f:
        try:
            state = json.load(f)
        except Exception:
            state = {}

    backup = state_path.with_suffix(".backup.json")
    with backup.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"[migrate_state] 💾 Backup saved: {backup.name}")

    state.setdefault("rotation", {"cat_i": 0, "seed_i": 0, "lt_i": 0})
    state.setdefault("used_pairs", [])
    state.setdefault("seen", state.get("seen", []))
    state.setdefault("used_links", state.get("used_links", []))
    state.setdefault("last_video_ids", state.get("last_video_ids", []))

    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"[migrate_state] ✅ Migration complete: {state_path}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    state_path = project_root / "blog_src" / "data" / "state.json"
    migrate_state(state_path)
