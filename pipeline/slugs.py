# pipeline/slugs.py
import re

def build_slug(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = text.replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
