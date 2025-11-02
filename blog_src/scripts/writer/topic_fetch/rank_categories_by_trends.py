# ============================================================
# File: blog_src/scripts/writer/topic_fetch/rank_categories_by_trends.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topic_fetch\rank_categories_by_trends.py
# ============================================================
"""
Rank sandpaper-related categories by popularity using Google Trends (pytrends),
with live progress logging, fallback seeds, autosave, and empty-category log.
"""

from __future__ import annotations
import os
import time
import json
import math
from pathlib import Path
from typing import List, Dict, Any

# --- Silence warnings ---
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=FutureWarning)

import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

from pytrends.request import TrendReq

# ------------ CONFIG ------------
REGION          = ""                  # "" = worldwide
TIMEFRAME       = "today 12-m"        # last 12 months
TOP_K_QUERIES   = 10
SLEEP_SEC       = 1.5                 # delay between requests
WEIGHT_RELATED  = 0.7
WEIGHT_TREND    = 0.3

USE_INLINE_CATEGORIES = True
CATEGORIES_JSON_PATH  = r"C:\Users\vladi\Documents\blog.equalle.com\categories_sandpaper_full.json"

OUT_DIR = Path(r"C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topic_fetch\out")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH  = OUT_DIR / "ranked_categories_trends.csv"
JSON_PATH = OUT_DIR / "ranked_categories_trends.json"
LOG_PATH  = OUT_DIR / "empty_categories.log"

# ------------ INLINE CATEGORIES ------------
INLINE_CATEGORIES: List[str] = [
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

# ------------ HELPERS ------------
def seeds_for_category(name: str) -> List[str]:
    """Generate multiple search seed queries per category to capture variations."""
    base = name.replace("&", "").replace("/", " ").strip()
    base_main = base.split()[0] if len(base.split()) > 0 else base

    candidates = [
        f"{base} sanding",
        f"{base} sandpaper",
        f"{base} abrasive",
        f"{base_main} sanding",
        f"{base_main} sandpaper",
    ]

    # Reinforce technical terms
    if "Grit" in name or "Education" in name:
        candidates.append("sandpaper grit")
        candidates.append("grit chart")
    if "Hook" in name or "PSA" in name:
        candidates.append("hook and loop sanding discs")
        candidates.append("psa sanding discs")
    if "Waterproof" in name or "Wet/Dry" in name:
        candidates.append("wet dry sandpaper")
    if "Discs" in name or "Formats" in name or "Belts" in name or "Pads" in name:
        candidates.extend(["sanding discs", "sanding belts", "sanding pads"])
    if "Dust" in name:
        candidates.extend(["dustless sanding", "hepa sanding vacuum"])
    if "Eco" in name:
        candidates.extend(["eco sandpaper", "non toxic sandpaper"])
    if "Innovation" in name:
        candidates.extend(["new abrasive technology", "abrasive research"])
    return list(dict.fromkeys(candidates))  # dedupe

def load_categories() -> List[str]:
    if USE_INLINE_CATEGORIES:
        return INLINE_CATEGORIES
    p = Path(CATEGORIES_JSON_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Categories JSON not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
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

def normalize_series(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return [1.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]

# ------------ CORE ------------
def rank_categories(categories: List[str]) -> pd.DataFrame:
    pytrends = TrendReq(hl="en-US", tz=360)
    rows: List[Dict[str, Any]] = []
    total = len(categories)
    empty_cats: List[str] = []
    start_time = time.time()

    for i, cat in enumerate(categories, start=1):
        print(f"\n▶ [{i}/{total}] Checking category: {cat}")
        cat_seeds = seeds_for_category(cat)
        related_sum = 0.0
        trend_vals: List[float] = []
        found_data = False

        for j, seed in enumerate(cat_seeds, start=1):
            print(f"   ⏳ Seed {j}/{len(cat_seeds)}: {seed}")
            try:
                pytrends.build_payload([seed], geo=REGION, timeframe=TIMEFRAME)
                rq_map = pytrends.related_queries()
                rq_df = rq_map.get(seed, {}).get("top")
                if rq_df is not None and not rq_df.empty:
                    val = float(rq_df.head(TOP_K_QUERIES)["value"].sum())
                    related_sum += val
                    found_data = True
                    print(f"     ✓ Related score: {val:.1f}")
                else:
                    print(f"     ⚠ No related queries")
            except Exception as e:
                print(f"     ⚠ Error fetching related queries: {e}")

            try:
                iot = pytrends.interest_over_time()
                if iot is not None and not iot.empty and seed in iot.columns:
                    vals = [float(x) for x in iot[seed].tail(90).tolist()]
                    if vals:
                        trend_vals.extend(vals)
                        found_data = True
                        print(f"     ✓ Trend points: {len(vals)}")
            except Exception as e:
                print(f"     ⚠ Error fetching interest_over_time: {e}")

            time.sleep(SLEEP_SEC)

        trend_mean = float(sum(trend_vals) / len(trend_vals)) if trend_vals else 0.0
        print(f"   ✅ Done {cat} → related_sum={related_sum:.1f}, trend_mean={trend_mean:.1f}")

        if not found_data:
            empty_cats.append(cat)

        rows.append({
            "category": cat,
            "related_raw": related_sum,
            "trend_raw": trend_mean,
        })

        # autosave after each category
        df_tmp = pd.DataFrame(rows)
        df_tmp["related_norm"] = normalize_series(df_tmp["related_raw"].tolist())
        df_tmp["trend_norm"]   = normalize_series(df_tmp["trend_raw"].tolist())
        df_tmp["score"] = WEIGHT_RELATED * df_tmp["related_norm"] + WEIGHT_TREND * df_tmp["trend_norm"]
        df_tmp = df_tmp.sort_values(["score", "related_norm", "trend_norm"], ascending=False)
        df_tmp.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
        df_tmp.to_json(JSON_PATH, orient="records", force_ascii=False, indent=2)

    # write empty-category log
    if empty_cats:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            for cat in empty_cats:
                f.write(cat + "\n")

    elapsed = time.time() - start_time
    print(f"\n⏱  Finished all {total} categories in {elapsed/60:.1f} min")

    df = pd.DataFrame(rows)
    df["related_norm"] = normalize_series(df["related_raw"].tolist())
    df["trend_norm"]   = normalize_series(df["trend_raw"].tolist())
    df["score"] = WEIGHT_RELATED * df["related_norm"] + WEIGHT_TREND * df["trend_norm"]
    df = df.sort_values(["score", "related_norm", "trend_norm"], ascending=False).reset_index(drop=True)
    return df

# ------------ MAIN ------------
def main():
    categories = load_categories()
    df = rank_categories(categories)

    df.to_json(JSON_PATH, orient="records", force_ascii=False, indent=2)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    print(f"\n✅ Saved final results:\n- {JSON_PATH}\n- {CSV_PATH}")
    if LOG_PATH.exists():
        print(f"⚠ Empty categories logged in: {LOG_PATH}")

    print("\n🏁 Top 10 categories by composite score:\n")
    print(df.head(10))

if __name__ == "__main__":
    main()
