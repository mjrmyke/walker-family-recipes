# pipeline/fractions.py
import math

_NICE = [(0.0, ""), (0.125, "⅛"), (0.25, "¼"), (1/3, "⅓"), (0.5, "½"),
         (2/3, "⅔"), (0.75, "¾"), (0.875, "⅞"), (1.0, "")]

def format_fraction(x: float) -> str:
    whole = math.floor(x + 1e-9)
    frac = x - whole
    value, label = min(_NICE, key=lambda p: abs(frac - p[0]))
    if abs(value - 1.0) < 1e-9:        # snapped up to next whole
        whole += 1; label = ""
    if label == "":
        return str(whole)
    return f"{whole} {label}" if whole else label
