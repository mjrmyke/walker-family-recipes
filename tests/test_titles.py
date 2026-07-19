# tests/test_titles.py
from pipeline.titles import parse_title, is_recipe_post

def test_parses_basic_title():
    r = parse_title("Week 28: Wild West - Cornbread and Baked Beans")
    assert r == {"week": 28, "theme": "Wild West",
                 "dish": "Cornbread and Baked Beans", "track": None}

def test_parses_meta_track():
    r = parse_title("Week 52: X, Y, and Z - Zesty Italian Chicken Sliders (Meta: Mindful Meals)")
    assert r["week"] == 52
    assert r["theme"] == "X, Y, and Z"
    assert r["dish"] == "Zesty Italian Chicken Sliders"
    assert r["track"] == "Mindful Meals"

def test_rejects_recap_and_removed():
    assert parse_title("Week 1 - 52: Challenge Complete for 2025!") is None
    assert is_recipe_post("52weeksofcooking", "[ Removed by moderator ]") is False
    assert is_recipe_post("excel", "Week 1: X - Y") is False

def test_accepts_valid_recipe_post():
    assert is_recipe_post("52weeksofcooking",
                          "Week 3: Contrasts - Tacos Two Ways") is True
