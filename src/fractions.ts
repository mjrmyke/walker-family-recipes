// Mirror of pipeline/fractions.py — snap a decimal to a nice culinary fraction.
const NICE: [number, string][] = [
  [0, ""], [0.125, "⅛"], [0.25, "¼"], [1 / 3, "⅓"], [0.5, "½"],
  [2 / 3, "⅔"], [0.75, "¾"], [0.875, "⅞"], [1, ""],
];

export function formatFraction(x: number): string {
  let whole = Math.floor(x + 1e-9);
  const frac = x - whole;
  let best = NICE[0];
  for (const p of NICE) {
    if (Math.abs(frac - p[0]) < Math.abs(frac - best[0])) best = p;
  }
  if (Math.abs(best[0] - 1) < 1e-9) {
    whole += 1;
    best = NICE[0];
  }
  if (best[1] === "") return String(whole);
  return whole ? `${whole} ${best[1]}` : best[1];
}
