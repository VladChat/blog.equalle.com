# ============================================================
# File: blog_src/scripts/writer/posts.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\posts.py
# ============================================================

import re
import pathlib
import random
from datetime import datetime
from pathlib import Path

from slugify import slugify

from .qa import qa_check
from .config_loader import load_writer_config


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

def _safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def make_slug(s: str) -> str:
    """
    Безопасный slug без слэшей — предотвращает создание вложенных директорий (Hugo).
    """
    if not s:
        return "post"
    s = slugify(s)[:80]
    s = s.replace("/", "-").replace("\\", "-")
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "post"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


# ────────────────────────────────────────────────────────────
# Public API used by writer
# ────────────────────────────────────────────────────────────

def gather_posts(content_dir: pathlib.Path):
    """
    Собирает метаданные постов для пула внутренних ссылок.
    Ожидается структура: content/posts/YYYY/MM/slug.md
    """
    cfg = load_writer_config()
    path_prefix = cfg.get("path_prefix", "")  # "" для eQualle/Nailak, "/blog" для проектов с префиксом

    posts = []
    for md in content_dir.rglob("*.md"):
        rel = md.relative_to(content_dir)
        if len(rel.parts) >= 3:
            y, m = rel.parts[0], rel.parts[1]
            slug = md.stem
            # Универсальный путь: корректно работает и на /blog/, и на корне
            url = f"{path_prefix}/posts/{y}/{m}/{slug}/"
            text = _safe_read_text(md)
            t = re.search(r'^title:\s*"(.*)"\s*$', text, flags=re.M)
            posts.append({"title": t.group(1) if t else slug, "url": url})
    return posts


def inject_links(md: str, pool: list, n_min: int, n_max: int) -> str:
    """
    Вставляет блоки 'See also: ...' равномерно по абзацам.
    """
    if not pool:
        return md

    n = max(0, min(n_max, n_min if n_min == n_max else random.randint(n_min, n_max)))
    if n == 0:
        return md

    from random import sample
    picks = sample(pool, min(n, len(pool)))
    paras = md.split("\n\n")
    step = max(1, len(paras) // (len(picks) + 1))
    for i, p in enumerate(picks, start=1):
        paras.insert(i * step, f"See also: [{p['title']}]({p['url']})")
    return "\n\n".join(paras)


# Проксируем QA наружу (для совместимости с main.py, который зовёт posts.qa_check)
def qa_check_proxy(md_text: str) -> dict:
    return qa_check(md_text)


# Хелпер для конфигурации — всё через единый loader
def get_config() -> dict:
    return load_writer_config()


# ────────────────────────────────────────────────────────────
# Save helpers (унифицированные под разные вызовы)
# ────────────────────────────────────────────────────────────

def _build_front_matter(title: str, category: str | None) -> str:
    now = datetime.now().isoformat()
    if category:
        return (
            f"---\n"
            f'title: "{title}"\n'
            f"categories: [\"{category}\"]\n"
            f"date: {now}\n"
            f"---\n\n"
        )
    return (
        f"---\n"
        f'title: "{title}"\n'
        f"date: {now}\n"
        f"---\n\n"
    )


def _determine_target_path(content_dir: Path, title: str) -> Path:
    """
    content_dir/YYYY/MM/slug.md
    """
    slug = make_slug(title)
    today = datetime.now()
    post_dir = content_dir / f"{today.year}" / f"{today.month:02d}"
    _ensure_dir(post_dir)
    return post_dir / f"{slug}.md"


# === Public: save_post_markdown (используется в main_local.py) ===
def save_post_markdown(content_dir: Path, title: str, body_md: str, category: str | None = None) -> Path:
    """
    Универсальный сейвер: фронт-маттер (title, category, date), затем Markdown.
    Возвращает полный путь к сохраненному файлу.
    """
    print("[eQualle POSTS][SAVE_MD][START] 💾 Saving Markdown post...")
    target = _determine_target_path(content_dir, title)
    fm = _build_front_matter(title, category)
    target.write_text(fm + body_md.strip() + "\n", encoding="utf-8")

    # 👇 ДОБАВЬ ЭТИ 4 СТРОКИ — ПРЯМО ПОСЛЕ write_text()
    try:
        target.touch(exist_ok=True)
        print(f"[eQualle POSTS][TOUCH] ⏱️ File timestamp updated to trigger Hugo reload.")
    except Exception as e:
        print(f"[eQualle POSTS][TOUCH][FAIL] ⚠️ {e}")

    try:
        size = target.stat().st_size
    except Exception:
        size = "NA"
    print(f"[eQualle POSTS][SAVE_MD][DONE] ✅ {target} (size={size})")
    return target



# === Back-compat: save_post (старые вызовы) ===
def save_post(content_dir: Path, title: str, body_md: str, category: str | None = None) -> Path:
    """
    Обратная совместимость с более старыми вызовами save_post(content_dir, title, body_md[, category]).
    Делегирует на save_post_markdown.
    """
    print("[eQualle POSTS][SAVE][INFO] Using back-compat save_post → delegating to save_post_markdown")
    return save_post_markdown(content_dir, title, body_md, category)


# === Optional: draft saver used by local experiments ===
def save_post_draft(content_dir: Path, markdown_content: str, author_name: str, author_style: str) -> Path:
    """
    Сохраняет черновик поста с front matter, включающим автора.
    Не используется основным пайплайном, но оставлен для локальных набросков.
    """
    print("[eQualle POSTS][DRAFT][START] 📝 Saving draft post...")
    today = datetime.now()
    filename = f"{today.strftime('%Y-%m-%d')}-draft.md"
    target_dir = content_dir / f"{today.year}" / f"{today.month:02d}"
    _ensure_dir(target_dir)
    path = target_dir / filename

    front_matter = (
        f"---\n"
        f'title: "Auto-Generated Draft"\n'
        f'date: "{today.isoformat()}"\n'
        f'author: "{author_name}"\n'
        f'style_hint: "{author_style}"\n'
        f'description: "Generated article by {author_name} for eQualle Blog."\n'
        f"draft: true\n"
        f"---\n\n"
    )

    path.write_text(front_matter + markdown_content.strip() + "\n", encoding="utf-8")
    try:
        size = path.stat().st_size
    except Exception:
        size = "NA"
    print(f"[eQualle POSTS][DRAFT][DONE] ✅ {path} (size={size})")
    return path
