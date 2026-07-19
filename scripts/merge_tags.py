# scripts/merge_tags.py
"""Combine data/tags_*.json (from the tag-pass subagents) into data/tags.json.
Validates every tag against TAG_VOCAB and checks all recipe ids are covered."""
import json, glob
from pipeline.config import DATA, RECIPES_JSON
from pipeline.tags import TAG_VOCAB

def main():
    merged = {}
    for path in sorted(glob.glob(str(DATA / "tags_*.json"))):
        part = json.load(open(path, encoding="utf-8"))
        merged.update(part)

    bad = {i: [t for t in tags if t not in TAG_VOCAB] for i, tags in merged.items()}
    bad = {i: t for i, t in bad.items() if t}
    if bad:
        print("INVALID tags (not in vocab):")
        for i, t in bad.items():
            print(f"  {i}: {t}")

    recipe_ids = {r["id"] for r in json.load(open(RECIPES_JSON, encoding="utf-8"))}
    missing = sorted(recipe_ids - set(merged))
    extra = sorted(set(merged) - recipe_ids)
    json.dump(merged, open(DATA / "tags.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"wrote data/tags.json with {len(merged)} entries")
    print(f"recipes: {len(recipe_ids)} | missing tags: {len(missing)} | extra ids: {len(extra)}")
    if missing:
        print("  MISSING:", missing)
    if extra:
        print("  EXTRA:", extra)

if __name__ == "__main__":
    main()
