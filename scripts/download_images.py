# scripts/download_images.py
"""Download one hero image per recipe and optimize to WebP.

Primary source is Reddit's own hosted preview (preview.images[0].source.url) — present
for ~all posts, high-res, and stable. Falls back to resolve_image_urls (imgur/i.redd.it)
when no preview exists. Writes public/images/<slug>-<id>.webp and data/image_map.json.
"""
import json, io, time
import requests
from PIL import Image
from pipeline.config import POSTS_JSON, IMAGES_DIR, DATA, RAW
from pipeline.images import resolve_image_urls, to_webp, is_placeholder_size

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")}

def preview_by_permalink() -> dict:
    raw = json.load(open(RAW / "submitted-1.json", encoding="utf-8"))
    out = {}
    for c in raw["data"]["children"]:
        d = c["data"]
        out[d["permalink"]] = d
    return out

def image_sources(post: dict, raw_post: dict) -> list[str]:
    if raw_post:
        imgs = (raw_post.get("preview") or {}).get("images") or []
        if imgs and imgs[0].get("source", {}).get("url"):
            return [imgs[0]["source"]["url"].replace("&amp;", "&")]
    return resolve_image_urls(post["url"], post)   # fallback

def fetch(url: str) -> bytes | None:
    if url.startswith("imgur-album:"):
        return None
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 200 and r.content:
            return r.content
    except requests.RequestException:
        pass
    return None

def main():
    posts = json.load(open(POSTS_JSON, encoding="utf-8"))
    raw_map = preview_by_permalink()
    updates = {}
    missing = []
    for i, p in enumerate(posts, 1):
        raw_post = raw_map.get(p["permalink"])
        image_path = None
        for url in image_sources(p, raw_post):
            raw = fetch(url)
            if not raw:
                continue
            try:
                size = Image.open(io.BytesIO(raw)).size
            except Exception:
                continue
            if is_placeholder_size(size):
                continue
            name = f"{p['slug']}-{p['id']}.webp"
            to_webp(raw, IMAGES_DIR / name, max_width=1200)
            image_path = f"images/{name}"
            break
        updates[p["id"]] = {"image": image_path, "gallery": []}
        if not image_path:
            missing.append(p["id"])
        print(f"[{i}/{len(posts)}] {'OK ' if image_path else 'XX '} {p['id']}")
        time.sleep(0.2)
    json.dump(updates, open(DATA / "image_map.json", "w", encoding="utf-8"), indent=2)
    print(f"\nimages done; {len(missing)} missing: {missing}")

if __name__ == "__main__":
    main()
