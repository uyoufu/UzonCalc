# Project Map
_Generated: 2026-06-16 17:34 | Git: 769a37e-dirty_

## Directory Structure
.agents/ - Local Codex skills, including the UzonCalc calculation-document writer.
dev_examples/ - Development examples, reference data, and engineering specification drafts.
examples/ - Public runnable examples and sample data used by README/demo flows.
scripts/ - Release, publish, and template-upload helper scripts.
src/core/ - Python workspace package for the calculation engine.
src/core/uzoncalc/ - Core runtime: context, AST instrumentation, formula rendering, units, template output.
src/core/uzoncalc/context_result_handler/ - Worktree module for final HTML result post-processing such as TOC generation.
src/core/uzoncalc/template/ - HTML template rendering, bundled browser assets, page styles, and document output glue.
src/core/uzoncalc/template/js/ - Bun/TypeScript browser bundle for document UI enhancements.
src/api/ - FastAPI backend workspace package for the desktop/web API and sandbox services.
src/web/ - Quasar/Vue frontend and Tauri desktop shell.
src/docs/ - Documentation site assets.
src/plans/ - Project planning documents.
tests/ - Core pytest suite for runtime, rendering, template, CLI, and example behavior.

## Key Files
AGENTS.md - Root agent constraints and module-specific AGENTS discovery rules.
pyproject.toml - Root uv workspace and root-only dev/preview dependency groups.
src/core/pyproject.toml - Published `uzoncalc` package metadata, dependencies, package-data rules, and test/publish groups.
src/core/uzoncalc/README.develop.md - High-value architecture map for the Python calculation pipeline.
src/core/uzoncalc/startup.py - `@uzon_calc()` entrypoint, context setup, and AST instrumentation handoff.
src/core/uzoncalc/context.py - `CalcContext` document state, content collection, options, cache access, and HTML output entrypoints.
src/core/uzoncalc/context_options.py - Document options for title, page size, margins, fonts, formatting, and handlers.
src/core/uzoncalc/context_utils/doc.py - User-facing document helpers for title, TOC, styles, head resources, and save/view flows.
src/core/uzoncalc/handcalc/ast_instrument.py - Reads source and compiles instrumented calculation functions.
src/core/uzoncalc/handcalc/recording_injector.py - Rewrites Python statements into record-step calls.
src/core/uzoncalc/handcalc/ast_to_ir.py - Converts Python AST expressions into MathIR for formula rendering.
src/core/uzoncalc/handcalc/rendering/equation_renderer.py - Renders assignment/expression steps with runtime values.
src/core/uzoncalc/handcalc/post_handlers/post_pipeline.py - Registers final string post-processing handlers.
src/core/uzoncalc/context_result_handler/toc.py - Generates TOC HTML from final body content in the current dirty worktree.
src/core/uzoncalc/template/utils.py - Injects body, page settings, resources, and options into the HTML template.
src/core/uzoncalc/template/calc_template.html - Base HTML shell consumed by rendered documents.
src/core/uzoncalc/template/js/package.json - Bun build script for the browser bundle.
src/core/uzoncalc/template/js/src/index.ts - Browser bootstrap for styles, figure labels, outline preview, scroll memory, and content patching.
src/api/AGENTS.md - API rule: controller/service responses to frontend must use i18n wrapper.
src/api/pyproject.toml - Backend package metadata and independent API runtime dependencies.
src/web/package.json - Quasar/Vue/Tauri frontend scripts and dependency baseline.

## Critical Constraints
- Before module work, check for a closer `AGENTS.md`; `src/api` and `src/core/uzoncalc/template/js` have extra rules.
- Root `pyproject.toml` manages the uv workspace only; root dev dependencies should not leak into core package metadata.
- Core package install/test loop: `uv sync --package uzoncalc --group test` then `uv run --package uzoncalc --group test pytest tests`.
- Template JS uses Bun, not npm/yarn/pnpm/node; run commands from `src/core/uzoncalc/template/js`.
- Rebuild `src/core/uzoncalc/template/js/dist/template.js` with `bun run build` before browser verification because Playwright reads the bundle.
- For template print/pagination regressions, Chromium/PDF output is the oracle; unit page counts alone are insufficient.
- Do not reintroduce legacy fragmentation fallback for the prior template pagination direction unless the user changes scope.
- API controller/service return values exposed to the frontend must be localized with the project i18n helper.
- Worktree was dirty when this map was generated; avoid treating current file layout as committed history.

## Hot Files
src/core/uzoncalc/context.py, src/core/uzoncalc/context_options.py, src/core/uzoncalc/context_result_handler/toc.py, src/core/uzoncalc/context_utils/doc.py, src/core/uzoncalc/template/utils.py, src/core/uzoncalc/template/calc_template.html, src/core/uzoncalc/template/js/src/index.ts, src/core/uzoncalc/template/js/src/styles/print.css, src/core/uzoncalc/template/js/dist/template.js, tests/test_context_result_handler_toc.py
