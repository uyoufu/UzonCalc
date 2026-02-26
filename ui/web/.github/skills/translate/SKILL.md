---
name: translate
description: translate frontend i18n from source language to target language
---

# Translate Skill

该技能用于在 `src/i18n/locales` 中进行多语言翻译与对齐。

## 目标

- 将某个语言文件翻译为其它语言文件, 可以调用 `scripts/compare_i18n.js` 来检查翻译结果与源语言的一致性
- 保证 key 的位置与顺序与源语言一致
- 结束后，需要重新调用 `scripts/compare_i18n.js` 来检查翻译结果与源语言的一致性

## 建议提示词

```text
将 [源语言] 增量翻译为 [目标语言]
```
