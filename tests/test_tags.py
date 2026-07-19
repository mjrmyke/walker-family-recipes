# tests/test_tags.py
from pipeline.tags import assign_tags, TAG_VOCAB

def test_protein_from_ingredients():
    tags = assign_tags(dish="Chicken Fajitas", theme="World Cup",
                       ingredient_items=["chicken breast", "peppers", "onion"])
    assert "chicken" in tags
    assert "mexican" in tags        # fajitas -> mexican cuisine keyword

def test_dessert_course():
    tags = assign_tags(dish="Peach Pie", theme="Gardening",
                       ingredient_items=["peaches", "flour", "butter", "sugar"])
    assert "dessert" in tags

def test_all_tags_are_in_vocab():
    tags = assign_tags(dish="Carne Asada Tacos", theme="Symmetry",
                       ingredient_items=["skirt steak", "lime", "cilantro"])
    assert set(tags).issubset(set(TAG_VOCAB))
    assert "beef" in tags
