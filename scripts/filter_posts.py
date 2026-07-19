# scripts/filter_posts.py
import json, glob
from pipeline.config import RAW, POSTS_JSON
from pipeline.titles import is_recipe_post, parse_title
from pipeline.slugs import build_slug
from datetime import datetime, timezone

def main():
    posts = []
    for path in sorted(glob.glob(str(RAW / "submitted-*.json"))):
        blob = json.load(open(path, encoding="utf-8"))
        for child in blob["data"]["children"]:
            d = child["data"]
            if not is_recipe_post(d["subreddit"], d["title"]):
                continue
            parsed = parse_title(d["title"])
            year = datetime.fromtimestamp(d["created_utc"], timezone.utc).year
            posts.append({
                "id": f"{'wc' if d['subreddit']=='52weeksofcooking' else 'wb'}"
                      f"-{year}-w{parsed['week']}",
                "week": parsed["week"], "year": year,
                "date": datetime.fromtimestamp(d["created_utc"], timezone.utc)
                        .strftime("%Y-%m-%d"),
                "theme": parsed["theme"], "dish": parsed["dish"],
                "title": d["title"], "track": parsed["track"],
                "subreddit": d["subreddit"],
                "redditUrl": "https://www.reddit.com" + d["permalink"],
                "permalink": d["permalink"], "url": d["url"],
                "slug": build_slug(parsed["dish"]),
                "num_comments": d["num_comments"],
                "media_metadata": d.get("media_metadata"),
                "gallery_data": d.get("gallery_data"),
                "is_gallery": d.get("is_gallery", False),
            })
    posts.sort(key=lambda p: (p["year"], p["week"]))
    json.dump(posts, open(POSTS_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"kept {len(posts)} recipe posts")

if __name__ == "__main__":
    main()
