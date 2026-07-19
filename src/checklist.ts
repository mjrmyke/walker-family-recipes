// Per-recipe ingredient checkbox state, persisted in localStorage.
const key = (id: string) => `wfr:checked:${id}`;

export function getChecked(id: string): Set<number> {
  try {
    return new Set<number>(JSON.parse(localStorage.getItem(key(id)) || "[]"));
  } catch {
    return new Set();
  }
}

export function setChecked(id: string, idx: number, on: boolean): void {
  const s = getChecked(id);
  if (on) s.add(idx);
  else s.delete(idx);
  localStorage.setItem(key(id), JSON.stringify([...s]));
}

export function resetChecked(id: string): void {
  localStorage.removeItem(key(id));
}
