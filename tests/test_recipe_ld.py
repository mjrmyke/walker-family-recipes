# tests/test_recipe_ld.py
from pipeline.recipe_ld import extract_recipe_ld

HTML_GRAPH = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
  {"@type":"WebPage","name":"blah"},
  {"@type":["Recipe","NewsArticle"],
   "name":"Best Banana Bread",
   "description":"Moist and easy.",
   "recipeYield":"1 loaf (8 servings)",
   "recipeIngredient":["2 cups flour","1/2 cup sugar","3 ripe bananas"],
   "recipeInstructions":[
     {"@type":"HowToSection","name":"Prep","itemListElement":[
        {"@type":"HowToStep","text":"Preheat oven to 350F."}]},
     {"@type":"HowToSection","name":"Bake","itemListElement":[
        {"@type":"HowToStep","text":"Mix and bake 50 minutes."}]}]}
]}
</script></head><body></body></html>
"""

HTML_SIMPLE = """
<script type="application/ld+json">
{"@type":"Recipe","name":"Simple","recipeYield":4,
 "recipeIngredient":["1 egg"],
 "recipeInstructions":"Just cook it."}
</script>
"""

HTML_LIST_STEPS = """
<script type="application/ld+json">
[{"@type":"Recipe","name":"Listy","recipeYield":["6"],
 "recipeIngredient":["a","b"],
 "recipeInstructions":[{"@type":"HowToStep","text":"Step one."},
                        {"@type":"HowToStep","text":"Step two."}]}]
</script>
"""

def test_extracts_graph_recipe_with_sections():
    r = extract_recipe_ld(HTML_GRAPH)
    assert r["name"] == "Best Banana Bread"
    assert r["description"] == "Moist and easy."
    assert r["ingredients"] == ["2 cups flour", "1/2 cup sugar", "3 ripe bananas"]
    assert r["steps"] == ["Preheat oven to 350F.", "Mix and bake 50 minutes."]
    assert r["servings"] == 8            # parsed from "1 loaf (8 servings)"

def test_extracts_simple_string_instructions():
    r = extract_recipe_ld(HTML_SIMPLE)
    assert r["ingredients"] == ["1 egg"]
    assert r["steps"] == ["Just cook it."]
    assert r["servings"] == 4

def test_extracts_list_of_howtosteps():
    r = extract_recipe_ld(HTML_LIST_STEPS)
    assert r["steps"] == ["Step one.", "Step two."]
    assert r["servings"] == 6

def test_returns_none_when_no_recipe():
    assert extract_recipe_ld("<html><body>no ld</body></html>") is None
