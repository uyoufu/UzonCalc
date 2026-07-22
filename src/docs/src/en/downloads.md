---
title: Downloads
editLink: false
description: Download the UzonCalc Windows desktop package to run calculation reports with automatic calculation, formula rendering, and document layout.
---

## 1.5.0

> Release date: 2026-07-22

### New Features

1. Isolated execution for calculation notebooks: absolute workspace imports are now automatically rewritten to package-relative form, allowing notebooks to run independently without relying on the full global workspace context.

### Download

[uzoncalc-win-x64-1.5.0.zip](https://oss.uzoncloud.com:2234/public/files/soft/uzoncalc-win-x64-1.5.0.zip)

## 1.4.0

> Release date: 2026-07-21

### New Features

1. Script notation now supports superscript and grouped operands, with prime character (′) as ungrouped superscript
2. Block LaTeX formulas are rendered with KaTeX for more professional display
3. Comparison operators (≥, ≤, ≠, etc.) are automatically converted to math symbols
4. New inline style helpers for bold, italic, and red/green/yellow colored text
5. Two-dimensional arrays are automatically rendered as matrix tables
6. New `uzoncalc zip` command to package scripts into .uzc archives, with shebang support for direct execution
7. New Figure helper with SVG graphic support
8. Workspace multi-tab support, in-place execution, and detached dependency editor
9. .uzc archives can be embedded in PNG thumbnails for easy preview and sharing

### Improvements

1. Added formula expression rendering toggle for flexible display control
2. Expression results can be captured and reused without re-evaluation
3. Share links are now persisted, surviving page refreshes
4. New favorites list and publish menu for easier report management
5. Redesigned pages with improved sharing and administration experience
6. Optimized internationalization and translations for clearer display
7. Core dependencies split into optional extras, reducing base installation size

### Bug Fixes

1. Fixed boolean values not rendering correctly in handcalc output
2. Fixed script notation matching failure after plain variables
3. Fixed incorrect unit reordering in table cells
4. Fixed top-level await calls being incorrectly recorded in formulas
5. Fixed type compatibility issue during .uzc packaging

### Download

[uzoncalc-win-x64-1.4.0.zip](https://oss.uzoncloud.com:2234/public/files/soft/uzoncalc-win-x64-1.4.0.zip)

## 1.3.0

> Release date: 2026-06-20

### Download

[uzoncalc-win-x64-1.3.0.zip](https://oss.uzoncloud.com:2234/public/files/soft/uzoncalc-win-x64-1.3.0.zip)
