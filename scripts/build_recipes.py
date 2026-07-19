# scripts/build_recipes.py
"""Merge posts + structured bodies + images into src/data/recipes.json.

Also:
  - de-duplicates cross-posted / repeated recipes (same dish) into one record that
    lists every posting (week/theme/subreddit) it appeared as, and
  - applies an authoritative tag file (data/tags.json, id -> [tags]) when present.
"""
import json, re
from pipeline.config import POSTS_JSON, STRUCTURED, RECIPES_JSON, DATA
from pipeline.assemble import merge_recipe
from pipeline.schema import validate_recipe
from pipeline.tags import TAG_VOCAB

TAGS_FILE = DATA / "tags.json"

def norm(dish: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", dish.lower()).strip()

def _components(recipes: list[dict]) -> list[list[dict]]:
    """Union recipes that are the same dish. Two recipes merge when they share a
    non-null recipe source URL, OR share a normalised dish name AND don't point at two
    different sources (so two different 'Chocolate Chip Cookies' recipes stay separate)."""
    parent = {r["id"]: r["id"] for r in recipes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    by_url: dict[str, list[str]] = {}
    for r in recipes:
        if r["sourceUrl"]:
            by_url.setdefault(r["sourceUrl"], []).append(r["id"])
    for ids in by_url.values():
        for i in ids[1:]:
            union(ids[0], i)

    by_dish: dict[str, list[dict]] = {}
    for r in recipes:
        by_dish.setdefault(norm(r["dish"]), []).append(r)
    for members in by_dish.values():
        urls = {m["sourceUrl"] for m in members if m["sourceUrl"]}
        if len(urls) <= 1:
            for m in members[1:]:
                union(members[0]["id"], m["id"])

    comps: dict[str, list[dict]] = {}
    for r in recipes:
        comps.setdefault(find(r["id"]), []).append(r)
    return list(comps.values())

def dedupe(recipes: list[dict]) -> list[dict]:
    """Merge same-recipe postings (cross-subreddit or repeated weeks) into one record."""
    out = []
    for members in _components(recipes):
        if len(members) == 1:
            out.append(members[0])
            continue
        # richest recipe supplies the content (ingredients/steps/image/description)
        best = sorted(members, key=lambda m: (
            not m["photoOnly"], len(m["ingredients"]), len(m["steps"]),
            not m["image"].endswith("placeholder.webp"), m["date"],
        ), reverse=True)[0]
        # most-recent posting supplies the headline week/theme (drives card + sorting)
        recent = max(members, key=lambda m: m["date"])
        rec = dict(best)
        for k in ("week", "year", "date", "theme", "subreddit", "redditUrl"):
            rec[k] = recent[k]
        # all postings, chronological
        seen, postings = set(), []
        for m in sorted(members, key=lambda m: (m["year"], m["week"])):
            for p in m["postings"]:
                key = (p["subreddit"], p["year"], p["week"])
                if key not in seen:
                    seen.add(key)
                    postings.append(p)
        rec["postings"] = postings
        # keep the other real photos as gallery
        gallery = list(rec.get("gallery", []))
        for m in members:
            if m["image"] != rec["image"] and not m["image"].endswith("placeholder.webp"):
                if m["image"] not in gallery:
                    gallery.append(m["image"])
        rec["gallery"] = gallery
        out.append(rec)
    return out

def main():
    posts = {p["id"]: p for p in json.load(open(POSTS_JSON, encoding="utf-8"))}
    imgs = json.load(open(DATA / "image_map.json", encoding="utf-8"))
    tags = json.load(open(TAGS_FILE, encoding="utf-8")) if TAGS_FILE.exists() else {}

    built, missing = [], []
    for pid, post in posts.items():
        body_path = STRUCTURED / f"{pid}.json"
        if not body_path.exists():
            missing.append(pid)
            continue
        body = json.load(open(body_path, encoding="utf-8"))
        body["tags"] = [t for t in body.get("tags", []) if t in TAG_VOCAB]  # drop stale tags
        built.append(merge_recipe(post, body, imgs.get(pid, {})))

    merged = dedupe(built)

    # apply authoritative tags, then re-validate
    for r in merged:
        if r["id"] in tags:
            r["tags"] = sorted(set(tags[r["id"]]))
            validate_recipe(r)

    merged.sort(key=lambda r: (r["year"], r["week"]))
    RECIPES_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump(merged, open(RECIPES_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    dupes = len(built) - len(merged)
    print(f"wrote {len(merged)} recipes ({dupes} duplicate postings merged) to {RECIPES_JSON}")
    if missing:
        print(f"MISSING structured body ({len(missing)}): {missing}")

if __name__ == "__main__":
    main()
