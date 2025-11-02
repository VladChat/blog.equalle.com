# ============================================================
# File: blog_src/scripts/writer/topic_fetch/rank_categories_by_trends_safe.py
# Full path: C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topic_fetch\rank_categories_by_trends_safe.py
# ============================================================
"""
Safer Google Trends harvester for category ranking (pytrends) that
tries to avoid IP throttling / 429 responses.

Key features:
- Global backoff + retry on HTTP 429 (and other transient errors)
- Minimum inter-request interval enforcement (rate limiting)
- Exponential backoff with jitter for retries
- Autosave after each category (CSV + JSON)
- Empty-category log
- Fallback seed generation
- Mild, configurable defaults tuned to avoid blocking

Usage:
    cd C:\Users\vladi\Documents\blog.equalle.com
    python .\blog_src\scripts\writer\topic_fetch\rank_categories_by_trends_safe.py

Adjust CONFIG below to tune timeouts/delays/retries.
"""

from __future__ import annotations
import time
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Any

# Silence noisy future warnings from pandas/pytrends
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=FutureWarning)

import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

from pytrends.request import TrendReq

# ---------------- CONFIG ----------------
# Safety / rate-limit tuning (defaults chosen to minimize 429 risk)
REGION = ""                       # worldwide
TIMEFRAME = "today 12-m"          # year
TOP_K_QUERIES = 10

MIN_REQUEST_INTERVAL = 10.0       # seconds between *consecutive* build_payload calls (critical)
BASE_SLEEP = 1.5                  # short sleep after successful seed processing (adds jitter)
MAX_RETRIES = 5                   # tries for transient errors (including 429)
BACKOFF_BASE = 8.0                # base seconds for exponential backoff on 429
BACKOFF_JITTER = 3.0              # add up to this value as random jitter
REQUEST_TIMEOUT = (10, 25)        # (connect, read) timeouts passed to TrendReq
TRENDREQ_RETRIES = 1              # pytrends internal retries (kept small)

# IO paths
OUT_DIR = Path(r"C:\Users\vladi\Documents\blog.equalle.com\blog_src\scripts\writer\topic_fetch\out")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUT_DIR / "ranked_categories_trends.csv"
JSON_PATH = OUT_DIR / "ranked_categories_trends.json"
LOG_PATH = OUT_DIR / "empty_categories.log"

# Inline categories (you can switch to a JSON source by changing load_categories)
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

# ------------- HELPERS -------------
def seeds_for_category(name: str) -> List[str]:
    base = name.replace("&", "").replace("/", " ").strip()
    base_main = base.split()[0] if base.split() else base
    candidates = [
        f"{base} sanding",
        f"{base} sandpaper",
        f"{base} abrasive",
        f"{base_main} sanding",
        f"{base_main} sandpaper",
    ]
    if "Grit" in name or "Education" in name:
        candidates += ["sandpaper grit", "grit chart"]
    if "Hook" in name or "PSA" in name:
        candidates += ["hook and loop sanding discs", "psa sanding discs"]
    if "Waterproof" in name or "Wet/Dry" in name:
        candidates += ["wet dry sandpaper"]
    if "Discs" in name or "Formats" in name or "Belts" in name or "Pads" in name:
        candidates += ["sanding discs", "sanding belts", "sanding pads"]
    if "Dust" in name:
        candidates += ["dustless sanding", "hepa sanding vacuum"]
    if "Eco" in name:
        candidates += ["eco sandpaper", "non toxic sandpaper"]
    return list(dict.fromkeys(candidates))

def normalize_series(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return [1.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]

# ---------------- Trend helper with robust retry/backoff ----------------
class TrendsClient:
    def __init__(self):
        # TrendReq supports timeout and a small retries param; we keep it small and handle retries here
        self.client = TrendReq(hl="en-US", tz=360, timeout=REQUEST_TIMEOUT, retries=TRENDREQ_RETRIES, backoff_factor=0.5)
        self._last_request_time = 0.0

    def _enforce_rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            wait_for = MIN_REQUEST_INTERVAL - elapsed
            print(f"   → Respecting rate limit: sleeping {wait_for:.1f}s before next request")
            time.sleep(wait_for)

    def safe_build_and_fetch(self, kw_list: List[str]) -> Dict[str, Any]:
        """
        Calls build_payload + related_queries + interest_over_time with retries/backoff.
        Returns a dict with keys:
           { 'related_map': <dict or None>, 'iot': <DataFrame or None>, 'error': <str or None> }
        """
        attempt = 0
        while attempt < MAX_RETRIES:
            attempt += 1
            try:
                self._enforce_rate_limit()
                # make the request
                self.client.build_payload(kw_list, geo=REGION, timeframe=TIMEFRAME)
                self._last_request_time = time.time()
                related_map = self.client.related_queries()
                iot = self.client.interest_over_time()
                return {'related_map': related_map, 'iot': iot, 'error': None}
            except Exception as e:
                errstr = str(e)
                # detect likely 429 (pytrends surfaces a message containing '429' or 'Too Many Requests')
                is_429 = '429' in errstr or 'Too Many Requests' in errstr or 'rate' in errstr.lower()
                print(f"     ⚠ Attempt {attempt}/{MAX_RETRIES} failed: {errstr.splitlines()[0]}")
                if is_429:
                    # exponential backoff with jitter
                    backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                    jitter = random.random() * BACKOFF_JITTER
                    sleep_for = backoff + jitter
                    print(f"       → Detected 429/rate-limit. Backing off {sleep_for:.1f}s (attempt {attempt})")
                    time.sleep(sleep_for)
                    # continue to retry
                    continue
                else:
                    # transient but non-429: small backoff and retry
                    sleep_for = 5.0 + random.random() * 3.0
                    print(f"       → Transient error, sleeping {sleep_for:.1f}s then retrying")
                    time.sleep(sleep_for)
                    continue
        # if we reach here, all retries exhausted
        return {'related_map': None, 'iot': None, 'error': 'max_retries_exceeded'}

# ---------------- CORE ----------------
def rank_categories(categories: List[str]) -> pd.DataFrame:
    tc = TrendsClient()
    rows: List[Dict[str, Any]] = []
    total = len(categories)
    empty_cats: List[str] = []
    start_time = time.time()

    for idx, cat in enumerate(categories, start=1):
        print(f"\n▶ [{idx}/{total}] Checking category: {cat}")
        seeds = seeds_for_category(cat)
        related_sum = 0.0
        trend_vals: List[float] = []
        found_any = False

        for s_idx, seed in enumerate(seeds, start=1):
            print(f"   ⏳ Seed {s_idx}/{len(seeds)}: {seed}")
            result = tc.safe_build_and_fetch([seed])
            if result['error']:
                print(f"     ⚠ Final error for seed: {result['error']}")
                # If max retries exceeded due to 429, be conservative: stop this category and continue after a long sleep
                if result['error'] == 'max_retries_exceeded':
                    long_sleep = BACKOFF_BASE * 2
                    print(f"       → Max retries reached. Sleeping long {long_sleep:.1f}s before next category")
                    time.sleep(long_sleep)
                    # we still continue to next seed/category (we don't abort whole run)
                continue

            related_map = result['related_map']
            iot = result['iot']

            # related queries
            try:
                rq_df = related_map.get(seed, {}).get('top') if related_map else None
                if rq_df is not None and not rq_df.empty:
                    val = float(rq_df.head(TOP_K_QUERIES)['value'].sum())
                    related_sum += val
                    found_any = True
                    print(f"     ✓ Related score: {val:.1f}")
                else:
                    print(f"     ⚠ No related queries")
            except Exception as e:
                print(f"     ⚠ Error parsing related queries: {e}")

            # interest over time
            try:
                if iot is not None and not iot.empty and seed in iot.columns:
                    vals = [float(x) for x in iot[seed].tail(90).tolist()]
                    if vals:
                        trend_vals.extend(vals)
                        found_any = True
                        print(f"     ✓ Trend points: {len(vals)}")
                else:
                    # sometimes interest_over_time returns DataFrame with different column naming;
                    # we won't attempt complicated heuristics here to avoid extra requests
                    pass
            except Exception as e:
                print(f"     ⚠ Error parsing interest_over_time: {e}")

            # short safe sleep after successful (or attempted) seed processing to avoid bursts
            time.sleep(BASE_SLEEP + random.random() * 0.8)

        trend_mean = float(sum(trend_vals) / len(trend_vals)) if trend_vals else 0.0
        print(f"   ✅ Done {cat} → related_sum={related_sum:.1f}, trend_mean={trend_mean:.1f}")

        if not found_any:
            empty_cats.append(cat)

        rows.append({
            'category': cat,
            'related_raw': related_sum,
            'trend_raw': trend_mean,
        })

        # autosave after each category
        df_partial = pd.DataFrame(rows)
        df_partial['related_norm'] = normalize_series(df_partial['related_raw'].tolist())
        df_partial['trend_norm'] = normalize_series(df_partial['trend_raw'].tolist())
        df_partial['score'] = WEIGHT_RELATED * df_partial['related_norm'] + WEIGHT_TREND * df_partial['trend_norm']
        df_partial = df_partial.sort_values(['score', 'related_norm', 'trend_norm'], ascending=False)
        df_partial.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
        df_partial.to_json(JSON_PATH, orient='records', force_ascii=False, indent=2)

    # write empty-category log
    if empty_cats:
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            for c in empty_cats:
                f.write(c + '\n')

    elapsed = time.time() - start_time
    print(f"\n⏱ Finished {len(categories)} categories in {elapsed/60:.1f} min")
    df = pd.DataFrame(rows)
    df['related_norm'] = normalize_series(df['related_raw'].tolist())
    df['trend_norm'] = normalize_series(df['trend_raw'].tolist())
    df['score'] = WEIGHT_RELATED * df['related_norm'] + WEIGHT_TREND * df['trend_norm']
    df = df.sort_values(['score', 'related_norm', 'trend_norm'], ascending=False).reset_index(drop=True)
    return df

# ---------------- MAIN ----------------
def main():
    categories = INLINE_CATEGORIES
    print("Starting safe trends harvest. This run is configured to be conservative to avoid 429s.")
    print(f"MIN_REQUEST_INTERVAL={MIN_REQUEST_INTERVAL}s, MAX_RETRIES={MAX_RETRIES}, BACKOFF_BASE={BACKOFF_BASE}s\n")
    df = rank_categories(categories)
    # final save (already saved incrementally, but ensure final files exist)
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    df.to_json(JSON_PATH, orient='records', force_ascii=False, indent=2)
    if LOG_PATH.exists():
        print(f"\n⚠ Empty categories logged: {LOG_PATH}")
    print(f"\n✅ Final results saved:\n - {CSV_PATH}\n - {JSON_PATH}")
    print("\nTop 10 by score:\n")
    print(df.head(10))

if __name__ == "__main__":
    main()
