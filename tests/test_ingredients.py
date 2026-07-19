# tests/test_ingredients.py
import math
from pipeline.ingredients import parse_quantity, parse_ingredient_line

def test_parse_quantity_forms():
    assert parse_quantity("2") == 2.0
    assert parse_quantity("1/2") == 0.5
    assert parse_quantity("1 1/2") == 1.5
    assert math.isclose(parse_quantity("⅔"), 2/3, abs_tol=1e-3)
    assert parse_quantity("2-3") == 2.0            # range -> low end
    assert parse_quantity("") is None

def test_line_qty_unit_item():
    assert parse_ingredient_line("2 cups flour") == \
        {"qty": 2.0, "unit": "cup", "item": "flour", "note": None}

def test_line_unicode_and_note():
    assert parse_ingredient_line("½ cup sugar, packed") == \
        {"qty": 0.5, "unit": "cup", "item": "sugar", "note": "packed"}

def test_line_no_unit():
    assert parse_ingredient_line("3 eggs") == \
        {"qty": 3.0, "unit": None, "item": "eggs", "note": None}

def test_glued_unicode_fraction():
    # "1½ tsp salt" — digit glued to fraction glyph (common on recipe blogs)
    r = parse_ingredient_line("1½ tsp salt")
    assert r["qty"] == 1.5
    assert r["unit"] == "tsp"
    assert r["item"] == "salt"
    assert parse_quantity("2¼") == 2.25

def test_parenthetical_note_keeps_inner_commas():
    r = parse_ingredient_line("2 ears of corn (husked, chopped)")
    assert r["qty"] == 2.0
    assert r["item"] == "ears of corn"
    assert r["note"] == "husked, chopped"

def test_nested_parenthetical_note():
    # RecipeTin-style: whole note wrapped in parens, sometimes with a nested paren
    r = parse_ingredient_line("3 cups day old jasmine rice (, cooked (Note 1))")
    assert r["qty"] == 3.0
    assert r["unit"] == "cup"
    assert r["item"] == "day old jasmine rice"
    assert r["note"] == "cooked (Note 1)"

def test_line_leading_thirds_fraction():
    # regression: char class must include ⅓/⅔ (recipes use thirds constantly)
    r = parse_ingredient_line("⅔ cup sugar")
    assert math.isclose(r["qty"], 2/3, abs_tol=1e-3)
    assert r["unit"] == "cup"
    assert r["item"] == "sugar"

def test_line_to_taste():
    assert parse_ingredient_line("Salt to taste") == \
        {"qty": None, "unit": None, "item": "Salt", "note": "to taste"}
