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

def test_line_to_taste():
    assert parse_ingredient_line("Salt to taste") == \
        {"qty": None, "unit": None, "item": "Salt", "note": "to taste"}
