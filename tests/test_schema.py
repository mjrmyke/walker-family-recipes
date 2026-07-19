# tests/test_schema.py
import pytest
from pipeline.schema import validate_recipe

VALID = {
    "id": "wc-2026-w28", "week": 28, "year": 2026, "date": "2026-07-13",
    "theme": "Wild West", "title": "Cornbread and Baked Beans",
    "dish": "Cornbread & Baked Beans", "subreddit": "52weeksofcooking",
    "track": None, "redditUrl": "https://reddit.com/x", "sourceUrl": None,
    "description": "Skillet cornbread with baked beans.",
    "image": "images/week-28-cornbread.webp", "gallery": [],
    "servings": 6,
    "ingredients": [{"qty": 1.0, "unit": "cup", "item": "cornmeal", "note": None}],
    "steps": ["Heat oven to 400F."], "tags": ["side", "bread"], "notes": None,
}

def test_valid_recipe_passes():
    validate_recipe(VALID)   # should not raise

def test_missing_field_fails():
    bad = {k: v for k, v in VALID.items() if k != "servings"}
    with pytest.raises(ValueError, match="servings"):
        validate_recipe(bad)

def test_bad_tag_fails():
    bad = {**VALID, "tags": ["not-a-real-tag"]}
    with pytest.raises(ValueError, match="tag"):
        validate_recipe(bad)

def test_empty_steps_fails():
    bad = {**VALID, "steps": []}
    with pytest.raises(ValueError, match="steps"):
        validate_recipe(bad)
