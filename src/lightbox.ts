// Full-image overlay. Click anywhere or press Esc to close.
export function openLightbox(src: string, alt = ""): void {
  const ov = document.createElement("div");
  ov.className = "lightbox";
  ov.innerHTML =
    `<img src="${src}" alt="${alt}"><button class="lb-close" aria-label="Close">✕</button>`;

  const close = () => {
    ov.remove();
    document.removeEventListener("keydown", onKey);
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") close();
  };

  ov.addEventListener("click", close);
  document.addEventListener("keydown", onKey);
  document.body.appendChild(ov);
}
