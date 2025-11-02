# ============================================================
# File: blog_src/scripts/writer/topic_fetch/rank_categories_by_trends.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topic_fetch\rank_categories_by_trends.py
# ============================================================
"""
Rank sandpaper-related categories by popularity using Google Trends (pytrends).

How it works:
- For each category, build several seed queries (category + "sanding", "sandpaper", etc.)
- Pull:
  (A) related_queries().top  -> sum of 'value' (top_k)
  (B) interest_over_time()   -> mean over timeframe (last 3 months)
- Composite score = 0.7 * related_norm + 0.3 * trend_norm
- Output sorted ranking to:
    - /mnt/data/ranked_categories_trends.json (also copied to project /tmp)
    - /mnt/data/ranked_categories_trends.csv

Requirements:
  pip install pytrends pandas

Notes:
- You can switch source of categories: INLINE list or JSON file.
- Be polite to Google: keep small sleep between calls.
"""

from __future__ import annotations
import os
import time
import json
import math
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from pytrends.request import TrendReq

# ------------ CONFIG ------------
REGION          = "US"
TIMEFRAME       = "today 3-m"         # last 3 months
TOP_K_QUERIES   = 10                  # how many related queries to aggregate per seed
SLEEP_SEC       = 2                   # be gentle to Trends
WEIGHT_RELATED  = 0.7                 # weight for related queries score
WEIGHT_TREND    = 0.3                 # weight for interest over time score

# Switch between INLINE categories or JSON file
USE_INLINE_CATEGORIES = True
CATEGORIES_JSON_PATH  = r"C:\Users\vladi\Documents\blog.equalle.com\categories_sandpaper_full.json"

# Inline list (union из “по применению” + “по продукту/материалам”)
INLINE_CATEGORIES: List[str] = [
    # Application-based
    "Woodworking & Furniture",
    "Automotive & Metalwork",
    "Drywall & Construction",
    "Paint Removal & Surface Prep",
    "Polishing & Finishing",
    "Plastic, Resin & Epoxy",
    "Marine & Outdoor Use",
    "Glass, Ceramics & Stone",
    "Industrial & Contractor",
    "Tools & Techniques",
    "Grit Guide & Education",
    "DIY & Home Projects",
    "Headlight Restoration",
    "Flooring & Wood Restoration",
    "Metal Polishing & Rust Repair",
    "Sanding Science & Experiments",
    "Painting & Coating Prep",
    "Dust Control & Safety",
    # Material/Product-based
    "Abrasive Materials & Compounds",
    "Backing Types & Coatings",
    "Sandpaper Shapes & Formats",
    "Hook & Loop vs PSA",
    "Grit Range & Classification",
    "Waterproof & Wet/Dry Paper",
    "Specialty Abrasives",
    "Sanding Belts & Machines",
    "Abrasive Accessories",
    "Dust Extraction & Vacuum Systems",
    "Industrial Abrasive Rolls & Bulk Packs",
    "Brand & Quality Comparison",
    "Eco & Non-Toxic Abrasives",
    "Surface Compatibility",
    "Performance & Longevity",
    "Abrasive Pads & Foam Systems",
    "Microfinishing & Polishing Films",
    "Abrasive Standards & Markings",
    "Sanding Tools & Power Systems",
    "Abrasive Innovation & Testing",
]

# Seeds per category: simple heuristic
# For каждой категории строим несколько seed-запросов, чтобы поймать разные формулировки.
def seeds_for_category(name: str) -> List[str]:
    base = name.replace("&", "").replace("/", " ").strip()
    candidates = [
        f"{base} sanding",
        f"{base} sandpaper",
        f"{base} abrasive",
    ]
    # Усилим для технических категорий
    if "Grit" in name or "Education" in name:
        candidates.append("sandpaper grit")
    if "Hook" in name or "PSA" in name:
        candidates.append("hook and loop sanding discs")
        candidates.append("psa sanding discs")
    if "Waterproof" in name or "Wet/Dry" in name:
        candidates.append("wet dry sandpaper")
    if "Discs" in name or "Formats" in name or "Belts" in name or "Pads" in name:
        candidates.append("sanding discs")
        candidates.append("sanding belts")
        candidates.append("sanding pads")
    if "Dust" in name:
        candidates.append("dustless sanding")
        candidates.append("hepa sanding vacuum")
    return list(dict.fromkeys(candidates))  # dedupe, preserve order

# ------------ DATA SOURCE ------------
def load_categories() -> List[str]:
    if USE_INLINE_CATEGORIES:
        return INLINE_CATEGORIES
    p = Path(CATEGORIES_JSON_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Categories JSON not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Accept either { "categories":[{"name":...},...] } or { "items": [...] } with "name"
    names: List[str] = []
    if isinstance(data, dict) and "categories" in data:
        for item in data["categories"]:
            name = item.get("name") or item.get("title")
            if name:
                names.append(name)
    elif isinstance(data, list):
        for item in data:
            name = item.get("name") or item.get("title")
            if name:
                names.append(name)
    else:
        raise ValueError("Unsupported JSON structure for categories.")
    return names

# ------------ SCORING ------------
def normalize_series(values: List[float]) -> List[float]:
    # Min-max normalization with protection against zero range
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return [1.0 for _ in values]  # all equal -> ones
    return [(v - vmin) / (vmax - vmin) for v in values]

def rank_categories(categories: List[str]) -> pd.DataFrame:
    pytrends = TrendReq(hl="en-US", tz=360)
    rows: List[Dict[str, Any]] = []

    for cat in categories:
        cat_seeds = seeds_for_category(cat)
        related_sum = 0.0
        trend_vals: List[float] = []

        for seed in cat_seeds:
            # related queries
            try:
                pytrends.build_payload([seed], geo=REGION, timeframe=TIMEFRAME)
                rq_map = pytrends.related_queries()
                rq_df = rq_map.get(seed, {}).get("top")
                if rq_df is not None and not rq_df.empty:
                    related_sum += float(rq_df.head(TOP_K_QUERIES)["value"].sum())
            except Exception:
                pass

            # interest over time
            try:
                iot = pytrends.interest_over_time()
                if iot is not None and not iot.empty and seed in iot.columns:
                    trend_vals.extend([float(x) for x in iot[seed].tail(90).tolist()])
            except Exception:
                pass

            time.sleep(SLEEP_SEC)

        trend_mean = float(sum(trend_vals) / len(trend_vals)) if trend_vals else 0.0
        rows.append({
            "category": cat,
            "related_raw": related_sum,
            "trend_raw": trend_mean,
        })

    df = pd.DataFrame(rows)

    # Normalization
    df["related_norm"] = normalize_series(df["related_raw"].tolist())
    df["trend_norm"]   = normalize_series(df["trend_raw"].tolist())

    # Composite score
    df["score"] = WEIGHT_RELATED * df["related_norm"] + WEIGHT_TREND * df["trend_norm"]

    # Sort by score desc
    df = df.sort_values(["score", "related_norm", "trend_norm"], ascending=False).reset_index(drop=True)
    return df

# ------------ MAIN ------------
def main():
    categories = load_categories()
    df = rank_categories(categories)

    # Save outputs near project and also to a neutral path (if needed)
    out_dir = Path(r"C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topic_fetch\out")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "ranked_categories_trends.json"
    csv_path  = out_dir / "ranked_categories_trends.csv"

    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"✅ Saved:\n- {json_path}\n- {csv_path}")
    print(df.head(10))

if __name__ == "__main__":
    main()
