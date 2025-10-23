# 💅 Nailak Blog — Technical Overview

This repository powers **blog.nailak.com**, the content and SEO platform of the **Nailak** beauty brand.  
It combines a **Hugo (PaperMod)** static site with a **Python-based generation pipeline** that automatically creates, enriches, and deploys blog content.

---

## 🧭 Project Structure

blog.nailak.com/
├── blog_src/ ← Hugo source directory
│ ├── archetypes/ ← Default front matter templates for new posts
│ ├── assets/ ← CSS, JS, and processed static assets
│ │ ├── css/
│ │ │ ├── colors.css ← Brand color palette & theme variables
│ │ │ ├── layout.css ← Containers, grids, sections, spacing
│ │ │ ├── typography.css ← Headings, paragraphs, typographic rhythm
│ │ │ ├── components.css ← Buttons, cards, banners, CTA blocks
│ │ │ └── ads.css ← Styling for ad cards and affiliate banners
│ │ └── js/
│ │ ├── custom/
│ │ │ ├── accordion.js ← Handles FAQ accordions + injects middle ad
│ │ │ ├── theme-toggle.js ← Switches light/dark theme
│ │ │ ├── analytics.js ← Google Tag Manager initialization
│ │ │ ├── lazyload.js ← Optional deferred image loading
│ │ │ └── aff-rotator.js ← Rotates affiliate ads if dynamic mode is enabled
│ │ └── vendor/ ← External libraries (if used)
│ ├── content/
│ │ └── posts/ ← Generated Markdown blog posts (AI pipeline)
│ ├── data/
│ │ ├── state.json ← Pipeline state (seen links, last_rss, counters)
│ │ ├── rss.json ← RSS feed sources for post generation
│ │ ├── keywords.json ← SEO keyword bank
│ │ ├── brand_images.json ← List of brand visuals for auto-injection
│ │ └── aff-cards.json ← Amazon affiliate ad card definitions
│ ├── layouts/ ← Hugo templates & partials
│ │ ├── _default/
│ │ │ ├── baseof.html ← Core HTML skeleton
│ │ │ ├── single.html ← Individual post layout
│ │ │ ├── list.html ← Post listing / homepage template
│ │ │ └── terms.html ← Tag/category term listings
│ │ ├── partials/
│ │ │ ├── head.html ← SEO meta, favicon, GTM, OG tags
│ │ │ ├── header.html ← Navigation bar and logo
│ │ │ ├── footer.html ← Footer, copyright, and social links
│ │ │ ├── custom/
│ │ │ │ ├── aff-rotator.html ← Ad block partial (top/bottom of posts)
│ │ │ │ └── schema.html ← Structured data (JSON-LD FAQ, etc.)
│ │ │ ├── toc.html ← Table of contents (if enabled)
│ │ │ └── breadcrumbs.html ← Navigation breadcrumbs
│ │ └── shortcodes/ ← Hugo shortcodes (used inside Markdown)
│ ├── scripts/ ← Python automation and content generation
│ │ ├── writer/
│ │ │ ├── main.py ← AI writer — generates Markdown posts
│ │ │ ├── brandimg_injector.py ← Injects brand images into post content
│ │ │ └── utils.py ← Common helper functions
│ │ ├── rss_fetch.py ← Fetches and deduplicates RSS feed items
│ │ └── debug_tools.py ← Optional local diagnostic helpers
│ ├── static/ ← Static, non-processed assets
│ │ ├── images/ ← Brand images (cuticle oil bottles, etc.)
│ │ ├── favicon.ico
│ │ ├── robots.txt
│ │ ├── sitemap.xml
│ │ └── manifest.json
│ ├── config.yml ← Main Hugo configuration (title, baseURL, etc.)
│ └── themes/PaperMod/ ← Base theme (untouched)
│
├── docs/ ← Final static output (Hugo publishDir)
├── .github/workflows/
│ ├── blog_writer.yml ← Runs Python AI writer via GitHub Actions
│ └── blog_build.yml ← Builds & deploys site to GitHub Pages
├── requirements.txt ← Python dependencies
└── README.md ← This documentation


---

## ⚙️ Content Pipeline

1. **RSS Fetch (`rss_fetch.py`)**  
   Loads feed URLs from `data/rss.json`, parses entries, filters duplicates using `state.json`, and returns a new topic.

2. **AI Writer (`writer/main.py`)**  
   - Uses OpenAI GPT-5 to generate SEO-optimized Markdown posts.  
   - Pulls keywords from `keywords.json`.  
   - Inserts metadata: title, date, description, tags.  
   - Saves file to `content/posts/.../index.md`.

3. **Brand Image Injector (`writer/brandimg_injector.py`)**  
   - Inserts Nailak brand visuals inside posts (intro and after 3rd section).  
   - Reads `brand_images.json`.  
   - Updates rotation counters in `state.json`.

4. **Hugo Build**  
   - Templates from `layouts/_default/` and partials render Markdown into HTML.  
   - CSS and JS processed via Hugo Pipes (minify + fingerprint).  
   - Outputs static site to `/docs` for publishing.

5. **Ad Integration**  
   - Top and bottom ads: `layouts/partials/custom/aff-rotator.html`  
   - Middle ad: dynamically injected by `accordion.js` after first section.  
   - Product data comes from `data/aff-cards.json`.

---

## 🧱 Styling System

| File | Role |
|------|------|
| **colors.css** | Defines brand colors, dark/light mode variables |
| **typography.css** | Sets font families, sizes, headings, spacing |
| **layout.css** | Handles structure, grids, containers, margins |
| **components.css** | Buttons, cards, CTAs, banners |
| **ads.css** | Visual styling for affiliate product blocks |

All CSS passes through **Hugo Pipes**, ensuring automatic minification and cache-busting fingerprints.

---

## 💻 JavaScript Logic

| File | Function |
|------|-----------|
| `accordion.js` | Expands FAQ sections, injects middle ad |
| `theme-toggle.js` | Switches theme and remembers user preference |
| `analytics.js` | Loads Google Tag Manager (GTM-PMFJ4Q24) |
| `aff-rotator.js` | Optional dynamic ad rotation (frontend) |
| `lazyload.js` | Defers image loading for performance |

---

## 🧩 Hugo Layouts and Partials

| File | Description |
|------|--------------|
| `_default/single.html` | Main post layout |
| `_default/list.html` | Post listing page (homepage, category, tag) |
| `partials/head.html` | SEO meta, OG tags, GTM scripts |
| `partials/custom/aff-rotator.html` | Amazon ad block partial |
| `partials/header.html` | Navigation header and logo |
| `partials/footer.html` | Footer with brand info |
| `partials/toc.html` | Table of contents (optional) |
| `partials/breadcrumbs.html` | Breadcrumb navigation |

---

## 🧠 Data and Automation Files

| File | Description |
|------|--------------|
| `state.json` | Tracks last RSS feed and seen URLs |
| `rss.json` | RSS feed list |
| `keywords.json` | Keyword bank for AI prompts |
| `brand_images.json` | Brand image list for injection |
| `aff-cards.json` | Amazon ad card info (title, image, link) |

---

## 🧰 Local Development

```powershell
# Go to project
cd "C:\Users\vladi\Documents\blog.nailak.com"

# Generate a post
python -m blog_src.scripts.writer.main

# Run local Hugo server
hugo server -s blog_src --minify

# Build production site
hugo -s blog_src --minify

Preview:
👉 http://localhost:1313/

🧾 Automation via GitHub Actions
Workflow	Purpose
blog_writer.yml	Runs Python AI generator on schedule or manual trigger
blog_build.yml	Builds Hugo site and publishes to GitHub Pages (/docs/)
🎨 Brand Palette
Element	Light Theme	Dark Theme
Primary	#2F5E3F	#7BB661
Accent	#F8C84A	#F8C84A
Background	#FFFFFF	#0F1A13
Surface	#F9FAF9	#1C2A1E
Text Primary	#1B1B1B	#F2F2F2
Text Secondary	#4A4A4A	#CFCFCF
🧩 SEO Configuration

Single H1 per page (auto-demoted extra headings).

<head> includes title, meta description, OG, and canonical.

Sitemap and robots.txt included in /static.

FAQ schema via partials/custom/schema.html.

GTM ID: GTM-PMFJ4Q24.

✅ Definition of Done

A post is considered ready when:

Markdown file created in /content/posts/...

Front matter includes title, date, tags, description

Brand images injected properly

Top/middle/bottom ads included

state.json updated (seen & last_rss)

Hugo build runs clean (hugo --minify)

SEO meta and canonical validated

🧱 Layer Overview
Layer 1 — Data         → JSON + Markdown
Layer 2 — Logic        → Python scripts
Layer 3 — Rendering    → Hugo layouts & partials
Layer 4 — Presentation → CSS & JS
Layer 5 — Deployment   → GitHub Actions → /docs