# ============================================================
# File: blog_src/scripts/social/post_to_meta.py
# Purpose: Create test (draft) posts for Instagram & Facebook
# ============================================================

"""
Post to Instagram and Facebook (Test Mode)
------------------------------------------
Creates draft Instagram media container and test Facebook post
without publishing live content.
"""

import os
import requests
import json

# === Load credentials from environment variables ===
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PAGE_ID = os.getenv("META_PAGE_ID")
IG_USER_ID = "1784142239487755"  # Instagram Business ID (equalleabrasives)

if not ACCESS_TOKEN or not PAGE_ID:
    raise SystemExit("❌ Missing environment variables: META_ACCESS_TOKEN or META_PAGE_ID")

def create_instagram_draft(image_url: str, caption: str):
    """Создаёт черновик поста в Instagram (контейнер без публикации)."""
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, params=params)
    data = response.json()
    print("📸 Instagram draft created:")
    print(json.dumps(data, indent=2))
    return data

def post_facebook_test(caption: str, link: str = None, image_url: str = None):
    """Публикует тестовый пост в Facebook (непубличный)."""
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed"
    params = {
        "message": caption,
        "access_token": ACCESS_TOKEN,
        "published": False  # ← делает пост невидимым (черновик)
    }
    if link:
        params["link"] = link
    if image_url:
        params["picture"] = image_url

    response = requests.post(url, params=params)
    data = response.json()
    print("📘 Facebook test post created:")
    print(json.dumps(data, indent=2))
    return data

# === Test run ===
if __name__ == "__main__":
    caption = "Testing Meta API connection from blog.equalle.com 🚀 #equalle"
    img = "https://equalle.com/images/sandpaper-hero.webp"
    link = "https://blog.equalle.com/posts/test-connection/"

    create_instagram_draft(img, caption)
    post_facebook_test(caption, link, img)
