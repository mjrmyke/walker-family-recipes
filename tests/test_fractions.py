# tests/test_fractions.py
from pipeline.fractions import format_fraction

def test_wholes():
    assert format_fraction(2.0) == "2"
    assert format_fraction(0.0) == "0"

def test_common_fractions():
    assert format_fraction(0.5) == "½"
    assert format_fraction(2/3) == "⅔"
    assert format_fraction(1/3) == "⅓"

def test_mixed_numbers():
    assert format_fraction(1.5) == "1 ½"
    assert format_fraction(1 + 1/3) == "1 ⅓"

def test_snaps_to_nearest_nice_fraction():
    assert format_fraction(0.34) == "⅓"     # 0.34 -> 1/3
    assert format_fraction(0.99) == "1"     # carries up
