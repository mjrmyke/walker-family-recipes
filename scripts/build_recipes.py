# scripts/build_recipes.py
"""Merge posts + structured bodies + image_map into the final src/data/recipes.json."""
import json
from pipeline.config import POSTS_JSON, STRUCTURED, RECIPES_JSON, DATA
from pipeline.assemble import merge_recipe

def main():
    posts = {p["id"]: p for p in json.load(open(POSTS_JSON, encoding="utf-8"))}
    imgs = json.load(open(DATA / "image_map.json", encoding="utf-8"))
    out, missing_body = [], []
    for pid, post in posts.items():
        body_path = STRUCTURED / f"{pid}.json"
        if not body_path.exists():
            missing_body.append(pid)
            continue
        body = json.load(open(body_path, encoding="utf-8"))
        out.append(merge_recipe(post, body, imgs.get(pid, {})))
    out.sort(key=lambda r: (r["year"], r["week"]))
    RECIPES_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(RECIPES_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"wrote {len(out)} recipes to {RECIPES_JSON}")
    if missing_body:
        print(f"MISSING structured body ({len(missing_body)}): {missing_body}")

if __name__ == "__main__":
    main()
