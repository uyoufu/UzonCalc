# template-js

Template bundle source for `uzoncalc/template/calc_template.html`.

`template.js` now injects the built-in template styles automatically. Extend styles by
adding a new `.css` file under `src/styles/` and importing it from `src/styles/index.ts`
with `with { type: "text" }`.

Recommended structure:
- `variables.css`: design tokens such as colors, spacing, radius and shadows
- `theme.css`: global element theme such as `body`, headings, links and lists
- feature files like `math.css`, `table.css`, `toc.css`: module-specific styles

Build:

```bash
bun run build
```
