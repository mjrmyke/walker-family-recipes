# tests/test_recipe_wprm.py
from pipeline.recipe_wprm import extract_recipe_wprm

WPRM_HTML = """
<div class="wprm-recipe-container">
  <h2 class="wprm-recipe-name">Apple Dumplings</h2>
  <span class="wprm-recipe-servings">8</span>
  <ul class="wprm-recipe-ingredients">
    <li class="wprm-recipe-ingredient">
      <span class="wprm-recipe-ingredient-amount">2</span>
      <span class="wprm-recipe-ingredient-unit">cups</span>
      <span class="wprm-recipe-ingredient-name">flour</span>
    </li>
    <li class="wprm-recipe-ingredient">
      <span class="wprm-recipe-ingredient-name">1 stick butter</span>
    </li>
  </ul>
  <ul class="wprm-recipe-instructions">
    <li class="wprm-recipe-instruction">
      <div class="wprm-recipe-instruction-text">Peel the apples.</div></li>
    <li class="wprm-recipe-instruction">
      <div class="wprm-recipe-instruction-text">Bake 40 minutes.</div></li>
  </ul>
</div>
"""

def test_extracts_wprm_recipe():
    r = extract_recipe_wprm(WPRM_HTML)
    assert r["name"] == "Apple Dumplings"
    assert r["servings"] == 8
    assert r["ingredients"] == ["2 cups flour", "1 stick butter"]
    assert r["steps"] == ["Peel the apples.", "Bake 40 minutes."]

def test_returns_none_without_wprm():
    assert extract_recipe_wprm("<html><body><p>nope</p></body></html>") is None
