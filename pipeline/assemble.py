# pipeline/assemble.py
from pipeline.schema import validate_recipe

def merge_recipe(post: dict, body: dict, img: dict) -> dict:
    r = {
        "id": post["id"], "week": post["week"], "year": post["year"],
        "date": post["date"], "theme": post["theme"], "title": post["title"],
        "dish": post["dish"], "subreddit": post["subreddit"],
        "track": post.get("track"), "redditUrl": post["redditUrl"],
        "sourceUrl": body.get("sourceUrl"), "description": body["description"],
        "image": (img or {}).get("image") or "images/placeholder.webp",
        "gallery": (img or {}).get("gallery", []), "servings": body["servings"],
        "ingredients": body["ingredients"], "steps": body["steps"],
        "tags": body["tags"], "notes": body.get("notes"),
        "photoOnly": body.get("photoOnly", False),
    }
    validate_recipe(r)
    return r
