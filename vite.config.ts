import { defineConfig } from "vite";

// Local dev/preview serve at "/"; the production build targets the GitHub Pages
// project subpath. import.meta.env.BASE_URL reflects this everywhere.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/walker-family-recipes/" : "/",
}));
