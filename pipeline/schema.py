# pipeline/schema.py
from pipeline.tags import TAG_VOCAB

_REQUIRED = ["id", "week", "year", "date", "theme", "title", "dish", "subreddit",
             "track", "redditUrl", "sourceUrl", "description", "image", "gallery",
             "servings", "ingredients", "steps", "tags", "notes", "photoOnly", "postings"]

_POSTING_KEYS = {"week", "year", "date", "theme", "subreddit", "redditUrl"}

def validate_recipe(r: dict) -> None:
    for f in _REQUIRED:
        if f not in r:
            raise ValueError(f"missing field: {f}")
    if not isinstance(r["photoOnly"], bool):
        raise ValueError("photoOnly must be a bool")
    if not r["postings"]:
        raise ValueError("postings must be non-empty")
    for p in r["postings"]:
        if not _POSTING_KEYS.issubset(p):
            raise ValueError(f"posting missing keys: {p}")
    for t in r["tags"]:
        if t not in TAG_VOCAB:
            raise ValueError(f"unknown tag: {t}")
    # Photo-only recipes (no recipe was ever posted) carry just image + metadata.
    if r["photoOnly"]:
        return
    # Full recipes must be cookable.
    if not isinstance(r["servings"], int) or r["servings"] <= 0:
        raise ValueError("servings must be a positive int")
    if not r["steps"]:
        raise ValueError("steps must be non-empty")
    if not r["ingredients"]:
        raise ValueError("ingredients must be non-empty")
    for ing in r["ingredients"]:
        if set(ing) != {"qty", "unit", "item", "note"}:
            raise ValueError(f"ingredient keys wrong: {ing}")
        if not ing["item"]:
            raise ValueError("ingredient item empty")
