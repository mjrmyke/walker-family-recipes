# tests/test_slugs.py
from pipeline.slugs import build_slug

def test_slug_basic():
    assert build_slug("Cornbread and Baked Beans") == "cornbread-and-baked-beans"

def test_slug_strips_punctuation_and_case():
    assert build_slug("Chili's Baby Back Ribs!") == "chilis-baby-back-ribs"

def test_slug_collapses_spaces_and_ampersand():
    assert build_slug("Mac  &  Cheese") == "mac-and-cheese"
