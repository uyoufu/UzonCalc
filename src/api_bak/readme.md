# UzonCalc API

## 编译多语言 PO 文件

项目运行时读取的是 `.mo` 文件，不会直接读取 `.po` 文件。因此修改翻译词条后，需要重新编译。

一键编译脚本位于 [scripts/compile-po.py](scripts/compile-po.py)。脚本会默认扫描 [app/locales](app/locales) 下所有 `LC_MESSAGES/messages.po`，并生成同目录下对应的 `.mo` 文件。

在 [ui/api](.) 目录执行：

```bash
python scripts/compile-po.py
```

只编译指定语言：

```bash
python scripts/compile-po.py --locale zh_CN
```

指定其他 domain：

```bash
python scripts/compile-po.py --domain messages
```

如果需要把 fuzzy 词条也编译进去：

```bash
python scripts/compile-po.py --use-fuzzy
```

默认目录约定如下：

- `.po` 文件：`app/locales/<locale>/LC_MESSAGES/<domain>.po`
- `.mo` 文件：`app/locales/<locale>/LC_MESSAGES/<domain>.mo`

当前项目的 i18n 配置位于 [app/i18n.py](app/i18n.py)，其中默认 domain 是 `messages`，locale 目录是 `app/locales`。

典型流程：

1. 在代码中使用 `_()` 包裹需要翻译的英文文案。
2. 在对应的 `.po` 文件中新增或修改 `msgid` / `msgstr`。
3. 执行 `python scripts/compile-po.py` 重新生成 `.mo`。
4. 重启服务并验证接口返回。