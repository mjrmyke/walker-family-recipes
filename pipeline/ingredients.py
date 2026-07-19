# pipeline/ingredients.py
import re

_UNICODE_FRAC = {"½":.5,"⅓":1/3,"⅔":2/3,"¼":.25,"¾":.75,"⅛":.125,"⅜":.375,"⅝":.625,"⅞":.875}

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
    note = None
    if "," in line:
        line, note = [p.strip() for p in line.split(",", 1)]
    # leading quantity: digits, unicode fractions, slashes, ranges
    m = re.match(r"^([\d\s./⅛¼⅜½⅝¾⅞–-]+)\s*(.*)$", line)
    qty, rest = None, line
    if m and parse_quantity(m.group(1)) is not None:
        qty = parse_quantity(m.group(1)); rest = m.group(2).strip()
    # unit
    unit = None
    parts = rest.split()
    if parts and parts[0].lower() in _UNIT_LOOKUP:
        unit = _UNIT_LOOKUP[parts[0].lower()]; rest = " ".join(parts[1:])
    # trailing "to taste" becomes a note
    if not note and rest.lower().endswith("to taste"):
        rest = rest[: -len("to taste")].strip(); note = "to taste"
    return {"qty": qty, "unit": unit, "item": rest.strip(), "note": note}
