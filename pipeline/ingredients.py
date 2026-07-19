# pipeline/ingredients.py
import re

_UNICODE_FRAC = {"½":.5,"⅓":1/3,"⅔":2/3,"¼":.25,"¾":.75,"⅛":.125,"⅜":.375,"⅝":.625,"⅞":.875}
_FRAC_CHARS = "".join(_UNICODE_FRAC)  # every fraction glyph, for the leading-qty char class

# canonical unit -> accepted spellings
_UNITS = {
    "cup": ["cups", "cup", "c"],
    "tsp": ["teaspoons", "teaspoon", "tsp", "tsps"],
    "tbsp": ["tablespoons", "tablespoon", "tbsp", "tbsps", "tbs"],
    "oz": ["ounces", "ounce", "oz"],
    "lb": ["pounds", "pound", "lbs", "lb"],
    "g": ["grams", "gram", "g"],
    "kg": ["kilograms", "kilogram", "kg"],
    "ml": ["milliliters", "milliliter", "ml"],
    "l": ["liters", "liter", "l"],
    "clove": ["cloves", "clove"],
    "can": ["cans", "can"],
    "pinch": ["pinches", "pinch"],
}
_UNIT_LOOKUP = {spell: canon for canon, spells in _UNITS.items() for spell in spells}

def parse_quantity(text: str):
    text = text.strip()
    if not text:
        return None
    text = text.split("-")[0].split("–")[0].strip()  # ranges -> low end
    text = re.sub(rf"(\d)([{_FRAC_CHARS}])", r"\1 \2", text)  # split glued "1½" -> "1 ½"
    total = 0.0
    matched = False
    for tok in text.split():
        if tok in _UNICODE_FRAC:
            total += _UNICODE_FRAC[tok]; matched = True
        elif re.fullmatch(r"\d+/\d+", tok):
            n, d = tok.split("/"); total += int(n) / int(d); matched = True
        elif re.fullmatch(r"\d+(\.\d+)?", tok):
            total += float(tok); matched = True
        else:
            break
    return total if matched else None

def parse_ingredient_line(line: str):
    line = line.strip().lstrip("-•*").strip()
    # leading quantity: digits, unicode fractions, slashes, ranges (incl. glued "1½")
    m = re.match(rf"^([\d\s./{_FRAC_CHARS}–-]+)\s*(.*)$", line)
    qty, rest = None, line
    if m and parse_quantity(m.group(1)) is not None:
        qty = parse_quantity(m.group(1)); rest = m.group(2).strip()
    # unit
    unit = None
    parts = rest.split()
    if parts and parts[0].lower() in _UNIT_LOOKUP:
        unit = _UNIT_LOOKUP[parts[0].lower()]; rest = " ".join(parts[1:])
    # note: a trailing parenthetical (taken outer-most, so nested "(, x (~ y))" works),
    # else a trailing comma clause
    note = None
    op = rest.find("(")
    stripped = rest.rstrip()
    if op != -1 and stripped.endswith(")"):
        inner = rest[op + 1: stripped.rfind(")")].strip().lstrip(",").strip()
        note = inner or None
        rest = rest[:op].strip()
    elif "," in rest:
        rest, note = [p.strip() for p in rest.split(",", 1)]
    # trailing "to taste" becomes a note
    if not note and rest.lower().endswith("to taste"):
        rest = rest[: -len("to taste")].strip(); note = "to taste"
    return {"qty": qty, "unit": unit, "item": rest.strip(), "note": note}
