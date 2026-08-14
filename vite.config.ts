import { defineConfig } from "vite";

// Served at the root of recipes.mykewalker.com (a GitHub Pages custom domain),
// so base is "/" for both dev and build. import.meta.env.BASE_URL reflects this
// everywhere via asset() in src/util.ts.
export default defineConfig({
  base: "/",
});
