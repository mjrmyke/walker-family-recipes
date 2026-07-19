# pipeline/recipe_ld.py
"""Extract a schema.org/Recipe from a page's JSON-LD.

Most recipe blogs embed a <script type="application/ld+json"> Recipe block with clean
recipeIngredient / recipeInstructions. This pulls it out deterministically so we don't
have to LLM-guess the ingredients.
"""
import json, re

_LD_BLOCK = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

def _iter_candidates(html: str):
    """Yield every JSON object found in the page's ld+json blocks (handles arrays/@graph)."""
    for block in _LD_BLOCK.findall(html):
        block = block.strip()
        try:
            data = json.loads(block)
        except (ValueError, json.JSONDecodeError):
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                if "@graph" in node and isinstance(node["@graph"], list):
                    stack.extend(node["@graph"])
                yield node

def _is_recipe(node: dict) -> bool:
    t = node.get("@type")
    if isinstance(t, list):
        return "Recipe" in t
    return t == "Recipe"

def _flatten_instructions(instr) -> list[str]:
    steps: list[str] = []
    if isinstance(instr, str):
        text = instr.strip()
        return [text] if text else []
    if isinstance(instr, list):
        for el in instr:
            if isinstance(el, str):
                if el.strip():
                    steps.append(el.strip())
            elif isinstance(el, dict):
                t = el.get("@type")
                if t == "HowToSection" or "itemListElement" in el:
                    steps.extend(_flatten_instructions(el.get("itemListElement", [])))
                else:
                    text = (el.get("text") or el.get("name") or "").strip()
                    if text:
                        steps.append(text)
    return steps

def _parse_servings(y) -> int | None:
    if isinstance(y, list):
        y = y[0] if y else None
    if isinstance(y, (int, float)):
        return int(y)
    if isinstance(y, str):
        m = re.search(r"(\d+)\s*serving", y, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m = re.search(r"\d+", y)
        if m:
            return int(m.group(0))
    return None

def extract_recipe_ld(html: str) -> dict | None:
    """Return {name, description, ingredients[str], steps[str], servings} or None."""
    for node in _iter_candidates(html):
        if not _is_recipe(node):
            continue
        ingredients = node.get("recipeIngredient") or node.get("ingredients") or []
        if isinstance(ingredients, str):
            ingredients = [ingredients]
        ingredients = [i.strip() for i in ingredients if isinstance(i, str) and i.strip()]
        steps = _flatten_instructions(node.get("recipeInstructions", []))
        if not ingredients and not steps:
            continue
        desc = node.get("description")
        return {
            "name": (node.get("name") or "").strip() or None,
            "description": desc.strip() if isinstance(desc, str) else None,
            "ingredients": ingredients,
            "steps": steps,
            "servings": _parse_servings(node.get("recipeYield")),
        }
    return None
