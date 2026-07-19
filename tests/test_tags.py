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

def test_vegetarian_only_for_savory_with_ingredients():
    veg = assign_tags(dish="Chickpea Coconut Curry", theme="Comfort",
                      ingredient_items=["chickpeas", "coconut milk", "spinach"])
    assert "vegetarian" in veg

def test_word_boundary_avoids_false_meat_tags():
    # "graham" must not trigger pork via "ham"; "rolled oats" must not trigger bread
    t = assign_tags(dish="S'mores Cheesecake", theme="Campfire",
                    ingredient_items=["graham crackers", "rolled oats", "chocolate"])
    assert "pork" not in t
    assert "bread" not in t
    # dessert with no meat should NOT be tagged vegetarian (uninformative)
    dessert = assign_tags(dish="Peach Pie", theme="Gardening",
                          ingredient_items=["peaches", "flour", "butter"])
    assert "vegetarian" not in dessert
    # photo-only (no ingredients known) should NOT be tagged vegetarian
    photo = assign_tags(dish="Mystery Dish", theme="Wildcard", ingredient_items=[])
    assert "vegetarian" not in photo

def test_all_tags_are_in_vocab():
    tags = assign_tags(dish="Carne Asada Tacos", theme="Symmetry",
                       ingredient_items=["skirt steak", "lime", "cilantro"])
    assert set(tags).issubset(set(TAG_VOCAB))
    assert "beef" in tags
