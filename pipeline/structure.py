# pipeline/structure.py
"""Build a structured recipe body from an external JSON-LD extraction (deterministic)
or a photo-only stub. LLM structuring (from Frankie's typed comment) is handled
separately and written straight to data/structured/<id>.json.
"""
import re
from pipeline.ingredients import parse_ingredient_line
from pipeline.tags import assign_tags

def first_sentence(text: str | None, maxlen: int = 160) -> str | None:
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m else text
    return s[:maxlen].strip()

def structure_from_external(post: dict, ext: dict) -> dict:
    ingredients = [parse_ingredient_line(line) for line in ext.get("ingredients", [])]
    ingredients = [i for i in ingredients if i["item"]]
    steps = [s for s in ext.get("steps", []) if s.strip()]
    servings = ext.get("servings")
    notes = None
    if not isinstance(servings, int) or servings <= 0:
        servings = 4
        notes = "servings estimated"
    desc = first_sentence(ext.get("description")) or f"{post['dish']} — a {post['theme']} week recipe."
    tags = assign_tags(post["dish"], post["theme"], [i["item"] for i in ingredients])
    return {
        "id": post["id"], "description": desc, "servings": servings,
        "ingredients": ingredients, "steps": steps, "tags": tags,
        "sourceUrl": post.get("recipe_url"), "notes": notes, "photoOnly": False,
    }

def structure_photoonly(post: dict, has_link: bool) -> dict:
    tags = assign_tags(post["dish"], post["theme"], [])
    return {
        "id": post["id"],
        "description": f"{post['dish']} — a {post['theme']} week recipe.",
        "servings": 0, "ingredients": [], "steps": [], "tags": tags,
        "sourceUrl": post.get("recipe_url") if has_link else None,
        "notes": "Photo only — see the original Reddit post.", "photoOnly": True,
    }
