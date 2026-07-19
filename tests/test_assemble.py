# tests/test_assemble.py
import pytest
from pipeline.assemble import merge_recipe

POST = {"id": "wc-2026-w28", "week": 28, "year": 2026, "date": "2026-07-13",
        "theme": "Wild West", "title": "Cornbread and Baked Beans",
        "dish": "Cornbread & Baked Beans", "subreddit": "52weeksofcooking",
        "track": None, "redditUrl": "https://reddit.com/x"}
BODY = {"id": "wc-2026-w28", "description": "Skillet cornbread.", "servings": 6,
        "ingredients": [{"qty": 1.0, "unit": "cup", "item": "cornmeal", "note": None}],
        "steps": ["Bake."], "tags": ["side", "bread"], "sourceUrl": None,
        "notes": None, "photoOnly": False}
IMG = {"image": "images/x.webp", "gallery": []}

def test_merge_produces_full_valid_record():
    r = merge_recipe(POST, BODY, IMG)
    assert r["id"] == "wc-2026-w28"
    assert r["description"] == "Skillet cornbread."
    assert r["image"] == "images/x.webp"
    assert r["servings"] == 6
    assert r["photoOnly"] is False
    assert set(r["ingredients"][0]) == {"qty", "unit", "item", "note"}

def test_merge_photoonly_uses_placeholder_when_no_image():
    body = {**BODY, "photoOnly": True, "ingredients": [], "steps": [], "servings": 0}
    r = merge_recipe(POST, body, {"image": None, "gallery": []})
    assert r["image"] == "images/placeholder.webp"
    assert r["photoOnly"] is True

def test_merge_rejects_invalid_body():
    bad = {**BODY, "tags": ["not-a-tag"]}
    with pytest.raises(ValueError):
        merge_recipe(POST, bad, IMG)
