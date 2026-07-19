# pipeline/recipe_wprm.py
"""Extract a recipe from WP Recipe Maker (WPRM) HTML.

Many food blogs render the recipe with WPRM's structured CSS classes but omit JSON-LD
(especially /wprm_print/ views). This parses those classes as a fallback to recipe_ld.
"""
import re
from bs4 import BeautifulSoup

def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()

def extract_recipe_wprm(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    ingredients = []
    for li in soup.select("li.wprm-recipe-ingredient"):
        parts = []
        for cls in ("amount", "unit", "name", "notes"):
            span = li.select_one(f".wprm-recipe-ingredient-{cls}")
            if span and _text(span):
                parts.append(_text(span))
        line = " ".join(parts).strip() or _text(li)
        if line:
            ingredients.append(line)

    steps = []
    for el in soup.select(".wprm-recipe-instruction-text"):
        t = _text(el)
        if t:
            steps.append(t)

    if not ingredients and not steps:
        return None

    name_el = soup.select_one(".wprm-recipe-name")
    serv_el = soup.select_one(".wprm-recipe-servings")
    servings = None
    if serv_el:
        m = re.search(r"\d+", _text(serv_el))
        if m:
            servings = int(m.group(0))

    return {
        "name": _text(name_el) if name_el else None,
        "description": None,
        "ingredients": ingredients,
        "steps": steps,
        "servings": servings,
    }
