# ============================================================
# File: blog_src/scripts/writer/social_cards.py
# Purpose:
#   - Generate social media cards (FB/IG/Pinterest/Twitter)
#   - Update Markdown front matter with card URLs
#   - Keep writer/main.py clean
# ============================================================

from __future__ import annotations

import yaml
from pathlib import Path
from datetime import datetime

# === Import existing card system (OLD CODE, WE REUSE IT) ===
from ..cards.core.models import Post as CardPost
from ..cards.core.registry import get_platforms
from ..cards.core.card_paths import (
    get_output_path,
    card_exists,
)
from ..cards.core.template_manager import get_next_template
from ..cards.update_front_matter import build_card_urls


# ============================================================
# 1. Generate all social cards for a new post
# ============================================================

def _generate_cards(slug: str, title: str, date: datetime, md_path: Path) -> dict:
    """
    Generates ALL social cards for this post using the existing card generator.
    Returns dict of platform→url (only paths, not prefixed with domain).
    """

    platforms = get_platforms()
    print(f"[social_cards] Platforms available: {[p.config.name for p in platforms]}")

    # Build a "CardPost" object (required by old generator)
    post = CardPost(
        slug=slug,
        title=title,
        date=date,
        source_path=md_path,
    )

    generated_paths = {}

    for platform in platforms:
        cfg = platform.config
        platform_name = cfg.name

        # Determine output location
        out_path = get_output_path(cfg, post)

        # Skip if already exists (writer re-run)
        if card_exists(cfg, post):
            print(f"[social_cards] [{platform_name}] Card already exists → {out_path}")
        else:
            template = get_next_template(cfg)
            print(f"[social_cards] [{platform_name}] Generating card using template: {template}")

            try:
                platform.generator(
                    post=post,
                    template_path=str(template),
                    output_path=str(out_path),
                    config=cfg,
                )
                print(f"[social_cards] [{platform_name}] ✔ Created: {out_path}")

            except Exception as e:
                print(f"[social_cards][ERROR] Card generation failed for {platform_name}: {e}")
                continue

        generated_paths[platform_name] = str(out_path)

    return generated_paths


# ============================================================
# 2. Inject card URLs into Markdown front matter
# ============================================================

def _update_markdown_with_cards(md_path: Path, cards_urls: dict):
    """
    Updates YAML front matter in the Markdown file.
    Adds 'cards:' section with URLs for fb/ig/pinterest/twitter.
    """

    text = md_path.read_text(encoding="utf-8")

    # Extract YAML front matter
    if not text.startswith("---"):
        print(f"[social_cards][WARN] No front matter in: {md_path}")
        return

    try:
        _, fm_text, body = text.split("---", 2)
    except ValueError:
        print(f"[social_cards][ERROR] Cannot split front matter in: {md_path}")
        return

    fm = yaml.safe_load(fm_text) or {}

    # Inject card URLs
    fm["cards"] = cards_urls

    # Rebuild YAML
    new_fm_text = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    new_content = f"---\n{new_fm_text}\n---\n{body.lstrip()}"

    md_path.write_text(new_content, encoding="utf-8")
    print(f"[social_cards] ✔ Markdown updated with cards section → {md_path}")


# ============================================================
# 3. Main wrapper: called from writer/main.py
# ============================================================

def generate_cards_and_update_markdown(
    slug: str,
    title: str,
    date: datetime,
    md_path: Path,
):
    """
    MAIN ENTRY POINT:
      - Generate all social cards
      - Build their URLs (using existing logic)
      - Patch Markdown front matter
    """

    print(f"\n[social_cards] === Generating cards for: {slug} ===")

    # 1. Generate JPG files
    _generate_cards(slug, title, date, md_path)

    # 2. Build URLs using existing helper (OLD code)
    try:
        urls = build_card_urls(slug, date)
        print("[social_cards] Built card URLs:")
        for k, v in urls.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"[social_cards][ERROR] URL build failed: {e}")
        return

    # 3. Update Markdown front matter
    _update_markdown_with_cards(md_path, urls)

    print(f"[social_cards] === Done for slug: {slug} ===\n")
