# pipeline/tags.py

# keyword -> canonical tag. First matching keyword adds the tag.
_KEYWORDS = {
    # protein
    "chicken": "chicken", "beef": "beef", "steak": "beef", "carne": "beef",
    "burger": "beef", "pork": "pork", "bacon": "pork", "carnitas": "pork",
    "shrimp": "seafood", "fish": "seafood", "salmon": "seafood", "egg": "egg",
    # course
    "pie": "dessert", "cake": "dessert", "cookie": "dessert", "ice cream": "dessert",
    "brownie": "dessert", "mousse": "dessert", "cupcake": "dessert",
    "bread": "bread", "naan": "bread", "roll": "bread", "biscuit": "bread",
    "soup": "soup", "ramen": "soup", "hot pot": "soup", "stew": "soup",
    "salad": "salad", "taco": "mexican", "fajita": "mexican", "asada": "mexican",
    "sauce": "sauce", "dip": "sauce", "chimichurri": "sauce",
    # cuisine
    "ramen ": "japanese", "sushi": "japanese", "plov": "central-asian",
    "shish": "middle-eastern", "taouk": "middle-eastern",
    # attribute
    "grill": "grill", "skewer": "grill", "baked": "baked",
}

TAG_VOCAB = sorted(set(_KEYWORDS.values()) | {
    "chicken", "beef", "pork", "seafood", "egg", "vegetarian",
    "dessert", "bread", "soup", "salad", "sauce", "side", "main",
    "mexican", "italian", "japanese", "middle-eastern", "central-asian",
    "grill", "baked", "quick",
})

def assign_tags(dish: str, theme: str, ingredient_items: list[str]) -> list[str]:
    haystack = " ".join([dish, theme, *ingredient_items]).lower()
    tags = []
    for kw, tag in _KEYWORDS.items():
        if kw.strip() in haystack and tag not in tags:
            tags.append(tag)
    return sorted(tags)
