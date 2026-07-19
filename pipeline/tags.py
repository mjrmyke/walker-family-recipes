# pipeline/tags.py
"""Suggest tags from a recipe's dish name, theme, and ingredients.

Two-tier to avoid noise:
  - DISH keywords (course/cuisine/style) match the dish + theme only, so an incidental
    ingredient never mislabels the course.
  - PROTEIN keywords match dish + ingredients (a recipe *with chicken* is a chicken recipe),
    EXCEPT egg, which only counts when the dish itself is egg-forward (eggs are incidental
    in most baking).
  - `vegetarian` is inferred when no meat/seafood protein is present.

Keywords match on word boundaries (+ optional plural) so "ham" doesn't fire on "graham"
and "roll" doesn't fire on "rolled".
"""
import re

# matched against dish + theme only
_DISH_KEYWORDS = {
    "pie": "dessert", "cake": "dessert", "cookie": "dessert", "ice cream": "dessert",
    "brownie": "dessert", "mousse": "dessert", "cupcake": "dessert", "pudding": "dessert",
    "tart": "dessert", "trifle": "dessert", "donut": "dessert", "doughnut": "dessert",
    "cheesecake": "dessert", "cobbler": "dessert", "crumble": "dessert", "macaron": "dessert",
    "bread": "bread", "naan": "bread", "roll": "bread", "biscuit": "bread", "bun": "bread",
    "loaf": "bread", "focaccia": "bread", "bagel": "bread", "breadstick": "bread",
    "soup": "soup", "ramen": "soup", "stew": "soup", "chowder": "soup", "pho": "soup",
    "bisque": "soup", "hot pot": "soup", "hotpot": "soup",
    "salad": "salad",
    "sauce": "sauce", "dip": "sauce", "dressing": "sauce", "chimichurri": "sauce",
    "salsa": "sauce", "vinaigrette": "sauce", "aioli": "sauce", "remoulade": "sauce",
    "taco": "mexican", "fajita": "mexican", "asada": "mexican", "burrito": "mexican",
    "enchilada": "mexican", "quesadilla": "mexican", "nacho": "mexican", "chimichanga": "mexican",
    "pasta": "italian", "pizza": "italian", "risotto": "italian", "lasagna": "italian",
    "gnocchi": "italian", "tortellini": "italian", "parmigiana": "italian", "ravioli": "italian",
    "sushi": "japanese", "teriyaki": "japanese", "miso": "japanese", "katsu": "japanese",
    "tempura": "japanese", "gyoza": "japanese", "ramen": "japanese",
    "plov": "central-asian",
    "shish": "middle-eastern", "taouk": "middle-eastern", "falafel": "middle-eastern",
    "hummus": "middle-eastern", "shawarma": "middle-eastern", "kebab": "middle-eastern",
    # style / attribute
    "grill": "grilled", "skewer": "grilled", "bbq": "grilled",
    "waffle": "baked", "muffin": "baked", "scone": "baked",
    # egg-forward dishes only (egg is incidental as an ingredient)
    "omelet": "egg", "omelette": "egg", "frittata": "egg", "quiche": "egg",
    "deviled egg": "egg", "shakshuka": "egg", "benedict": "egg",
}

# matched against dish + ingredients
_PROTEIN_KEYWORDS = {
    "chicken": "chicken", "beef": "beef", "steak": "beef", "carne": "beef",
    "burger": "beef", "brisket": "beef", "meatball": "beef", "ground beef": "beef",
    "pork": "pork", "bacon": "pork", "carnitas": "pork", "ham": "pork",
    "sausage": "pork", "prosciutto": "pork", "ribs": "pork",
    "lamb": "lamb", "turkey": "turkey",
    "shrimp": "seafood", "salmon": "seafood", "tuna": "seafood",
    "crab": "seafood", "scallop": "seafood",
}

_MEAT_TAGS = {"chicken", "beef", "pork", "lamb", "turkey", "seafood"}

# The controlled vocabulary. The LLM tag pass (data/tags.json) picks from exactly this set.
TAG_VOCAB = sorted({
    # protein
    "chicken", "beef", "pork", "lamb", "turkey", "seafood", "egg",
    # diet
    "vegetarian",
    # course
    "main", "side", "dessert", "bread", "soup", "salad", "sauce", "breakfast",
    # cuisine
    "mexican", "italian", "japanese", "chinese", "korean", "thai", "indian",
    "middle-eastern", "french", "central-asian",
    # attribute
    "spicy", "grilled", "baked", "quick",
})

def assign_tags(dish: str, theme: str, ingredient_items: list[str]) -> list[str]:
    dish_hay = f"{dish} {theme}".lower()
    ing_hay = " ".join(ingredient_items).lower()
    tags: list[str] = []

    def add(tag):
        if tag not in tags:
            tags.append(tag)

    def has(kw, hay):
        return re.search(rf"\b{re.escape(kw)}s?\b", hay) is not None

    for kw, tag in _DISH_KEYWORDS.items():
        if has(kw, dish_hay):
            add(tag)
    for kw, tag in _PROTEIN_KEYWORDS.items():
        if has(kw, dish_hay) or has(kw, ing_hay):
            add(tag)

    # `vegetarian` only for savory dishes we actually have ingredients for — not desserts,
    # breads, or photo-only cards (empty ingredient list) where the tag is uninformative.
    if (ingredient_items and not any(t in _MEAT_TAGS for t in tags)
            and not ({"dessert", "bread"} & set(tags))):
        add("vegetarian")

    return sorted(tags)
