# pipeline/images.py
import re
from pipeline.config import IMGUR_PLACEHOLDER_SIZE

_IMGUR_ALBUM = re.compile(r"imgur\.com/(?:a|gallery)/(\w+)")
_IMGUR_SINGLE = re.compile(r"imgur\.com/(\w+)(\.\w+)?$")

def _clean(u: str) -> str:
    return u.replace("&amp;", "&")

def resolve_image_urls(url: str, post: dict) -> list[str]:
    """Ordered list of direct, downloadable image URLs for a post.

    Album resolution (imgur.com/a/<id>) requires the album's member ids, which are
    fetched during harvest and attached to `post['imgur_album_images']`. If absent,
    the album id is returned as a marker for the harvest step to fill in.
    """
    # Reddit native gallery
    if post.get("is_gallery") and post.get("media_metadata"):
        order = [it["media_id"] for it in post.get("gallery_data", {}).get("items", [])]
        return [_clean(post["media_metadata"][mid]["s"]["u"]) for mid in order
                if mid in post["media_metadata"]]

    # Direct reddit image
    if "i.redd.it/" in url:
        return [url]

    # imgur album -> use pre-fetched member images if harvest attached them
    m = _IMGUR_ALBUM.search(url)
    if m:
        imgs = post.get("imgur_album_images")
        if imgs:
            return imgs
        return [f"imgur-album:{m.group(1)}"]  # marker; harvest resolves this

    # imgur single
    m = _IMGUR_SINGLE.search(url)
    if m:
        ext = m.group(2) or ".jpeg"
        return [f"https://i.imgur.com/{m.group(1)}{ext}"]

    return [url]  # already-direct or unknown; downloader will validate

def is_placeholder_size(size: tuple[int, int]) -> bool:
    """True if a decoded image is the imgur 'removed' placeholder or suspiciously tiny."""
    if size == IMGUR_PLACEHOLDER_SIZE:
        return True
    w, h = size
    return w < 64 or h < 64


import io
from pathlib import Path
from PIL import Image

def to_webp(raw: bytes, out_path: Path, max_width: int = 1200) -> tuple[int, int]:
    """Decode bytes, downscale to max_width, save as WebP. Returns final (w, h)."""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    if img.width > max_width:
        h = round(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "WEBP", quality=82, method=6)
    return img.size
