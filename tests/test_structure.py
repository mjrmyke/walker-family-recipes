# tests/test_structure.py
from pipeline.structure import structure_from_external, structure_photoonly

POST = {"id": "wc-2026-w4", "theme": "Vinegar", "dish": "Sweet & Sour Chicken",
        "recipe_url": "https://example.com/swsc"}
EXT = {"ok": True, "name": "Sweet and Sour Chicken",
       "description": "Crispy chicken in a tangy glaze. Ready in 30 minutes.",
       "ingredients": ["2 cups flour", "1 lb chicken breast, cubed", "Salt to taste"],
       "steps": ["Fry the chicken.", "Toss in sauce."], "servings": 4}

def test_structure_from_external_builds_body():
    b = structure_from_external(POST, EXT)
    assert b["id"] == "wc-2026-w4"
    assert b["photoOnly"] is False
    assert b["servings"] == 4
    assert b["sourceUrl"] == "https://example.com/swsc"
    assert len(b["ingredients"]) == 3
    assert b["ingredients"][1] == {"qty": 1.0, "unit": "lb",
                                   "item": "chicken breast", "note": "cubed"}
    assert b["steps"] == ["Fry the chicken.", "Toss in sauce."]
    assert "chicken" in b["tags"]
    assert b["description"] == "Crispy chicken in a tangy glaze."   # first sentence

def test_external_defaults_servings_when_missing():
    b = structure_from_external(POST, {**EXT, "servings": None})
    assert b["servings"] == 4
    assert b["notes"] == "servings estimated"

def test_photoonly_stub():
    b = structure_photoonly(POST, has_link=True)
    assert b["photoOnly"] is True
    assert b["ingredients"] == [] and b["steps"] == []
    assert b["servings"] == 0
    assert b["sourceUrl"] == "https://example.com/swsc"

def test_photoonly_without_link():
    b = structure_photoonly({**POST, "recipe_url": None}, has_link=False)
    assert b["sourceUrl"] is None
