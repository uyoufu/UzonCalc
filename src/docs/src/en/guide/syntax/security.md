---
title: Encryption and Formula Hiding
icon: lock
order: 10
---

## Hiding Formula Output

Some code is only used to organize data or call external resources and should not be displayed as formulas. Use hiding controls to manage output.

A common pattern is wrapping hidden code with `hide()` and `show()`:

```python
hide()
temporary_value = 1 + 2
show()

"The body text continues normally."
```

## Document Encryption

The UzonCalc documentation site includes VuePress page encryption examples for protecting documentation pages. If a calculation report needs access control, handle it in the deployment environment or file distribution workflow.

## Writing Tips

- Keep key calculation steps visible whenever possible so they can be reviewed.
- Hide data preparation, chart configuration, and external resource paths when they are not meaningful to readers.
- Do not write secrets, accounts, or internal addresses directly into reports.
