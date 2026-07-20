---
title: Table of Contents and Numbering
icon: list-ol
order: 6
---

## Automatic Table of Contents

Call `toc()` to generate a table of contents at the current position:

```python
toc("Contents")
```

The table of contents is generated from the report heading hierarchy, and page numbers are calculated during export or printing.

## Automatic Figure and Table Numbering

When you insert charts or tables with functions such as `Img()`, `Table()`, `EChart()`, and `Plot()`, UzonCalc maintains figure and table numbers automatically. These functions return a numbering placeholder that can be referenced later:

```python
img_no = Img(
    "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
    alt="UzonCalc run result",
)

f"Now you can reference this image: see {img_no}."
```

When rendered, the placeholder is replaced by the actual number and can link back to the corresponding chart or table.

## Changing Number Prefixes

Figure number prefixes can be changed:

```python
figure_prefix("Figure")

img_no = Img(
    "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
    alt="UzonCalc run result",
)

f"Now reference the image: see {img_no}."

figure_prefix("图")
```

Use `table_prefix("Table")` for table prefixes. Prefix settings affect later figures or tables, so it is best to set them near the beginning of the report.
