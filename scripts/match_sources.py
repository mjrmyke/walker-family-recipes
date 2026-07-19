# scripts/match_sources.py
"""Match Frankie's comments to filtered posts, build per-recipe source work-list.

Output: data/posts_sources.json — each item = post fields + Frankie's comment body,
the best external recipe URL (if any), and any video link. This is the input to the
structuring step (external JSON-LD extraction preferred, comment text as fallback).
"""
import json, re
from pipeline.config import RAW, DATA

POSTS = DATA / "posts.json"
COMMENTS = RAW / "frankie-comments.json"
OUT = DATA / "posts_sources.json"

# hosts that are NOT external recipe pages
NON_RECIPE_HOSTS = ("imgur.com", "i.imgur.com", "i.redd.it", "reddit.com",
                    "redd.it", "v.redd.it", "preview.redd.it")
VIDEO_HOSTS = ("youtube.com", "youtu.be", "m.youtube.com")

def postid_from_permalink(permalink: str) -> str | None:
    m = re.search(r"/comments/([a-z0-9]+)/", permalink)
    return m.group(1) if m else None

def host_of(url: str) -> str:
    m = re.match(r"https?://([^/]+)/?", url)
    return m.group(1).replace("www.", "") if m else ""

def classify(urls):
    recipe, video = None, None
    for u in urls:
        u = u.rstrip(").,]")
        h = host_of(u)
        if any(h.endswith(v) for v in VIDEO_HOSTS):
            video = video or u
        elif not any(h.endswith(n) for n in NON_RECIPE_HOSTS):
            recipe = recipe or u
    return recipe, video

def main():
    posts = json.load(open(POSTS, encoding="utf-8"))
    comments = json.load(open(COMMENTS, encoding="utf-8"))["comments"]

    # postid -> Frankie's comments, longest body first
    by_post = {}
    for c in comments:
        if c.get("author") != "Frankiieee":
            continue
        pid = (c.get("link_id") or "").replace("t3_", "")
        by_post.setdefault(pid, []).append(c)
    for pid in by_post:
        by_post[pid].sort(key=lambda c: len(c["body"]), reverse=True)

    out, no_comment, with_recipe, with_video = [], [], 0, 0
    for p in posts:
        pid = postid_from_permalink(p["permalink"])
        cmts = by_post.get(pid, [])
        body = cmts[0]["body"] if cmts else ""
        urls = []
        for c in cmts:
            urls += c.get("urls", [])
        recipe_url, video_url = classify(urls)
        if not cmts:
            no_comment.append(p["id"])
        if recipe_url:
            with_recipe += 1
        if video_url:
            with_video += 1
        out.append({**p, "comment_body": body,
                    "recipe_url": recipe_url, "video_url": video_url})

    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"posts: {len(out)}")
    print(f"  with Frankie comment: {len(out) - len(no_comment)}")
    print(f"  with external recipe URL: {with_recipe}")
    print(f"  with video URL: {with_video}")
    print(f"  NO comment matched ({len(no_comment)}): {no_comment}")

if __name__ == "__main__":
    main()
