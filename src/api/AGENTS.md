# uzoncalc api

为 uzoncalc web 端提供 api 接口，开发时需要遵循以下要求：

## 代码风格

- 使用枚举表示状态、禁止使用魔法字符串


## 列表分页接口

- 服务端分页列表统一提供同一路由前缀下的 `GET /count` 和 `GET /items`，不要返回同时包含总数和行数据的组合分页对象。
- `/count` 只接收业务筛选条件并返回 `ResponseResult[int]`，不接收分页参数。
- `/items` 接收与 `/count` 完全相同的业务筛选条件，并通过 FastAPI 依赖注入复用 `app.controller.dto_base.PaginationDTO`，返回 `ResponseResult[list[DTO]]`。
- Controller 和 service 不得重复声明 `skip`、`limit`、`sortBy`、`descending`；需要分页时直接传递 `PaginationDTO`。
- `/count` 和 `/items` 必须复用筛选 DTO 或筛选条件构造函数，确保用户隔离、软删除、分类和关键字等条件保持一致。
- `sortBy` 必须通过资源级白名单映射为 ORM 字段，禁止将请求字符串直接拼入 SQL；未知字段回退到资源默认排序，并追加唯一字段作为稳定次排序。
- 列表接口测试至少覆盖筛选一致性、分页边界、升降序、未知排序回退，以及静态 `/count`、`/items` 路由不会被动态对象路由捕获。

## 多语言

controller 和 service 层中，对前端返回的用户可见文案都应进行多语言适配，使用
`src/api/app/i18n.py` 中的 `_(message: str)` 函数。`_()` 中必须使用稳定的英文原文：
英文原文是 gettext 的 `msgid`，中文翻译是 `msgstr`。

### 翻译维护

AI 不得手工编辑 `app/locales/**/messages.po` 或 `messages.mo`。新增、修改、删除翻译时，
必须在仓库根目录通过 `src/api/scripts/upsert_i18n.py` 完成；脚本发生有效变更后会自动编译
同目录下的 `.mo` 文件。

批量新增或修改翻译时，重复传入 `--pair MSGID MSGSTR`：

```bash
uv run --package uzoncalc-api python src/api/scripts/upsert_i18n.py \
  --pair "Category not found" "分类不存在" \
  --pair "Report name '{name}' already exists" "报告名称 '{name}' 已存在"
```

批量删除翻译时，重复传入 `--delete MSGID`；不存在的词条会被忽略：

```bash
uv run --package uzoncalc-api python src/api/scripts/upsert_i18n.py \
  --delete "Category not found" \
  --delete "Report name '{name}' already exists"
```

使用脚本时还必须遵循以下约束：

- 包含空格或特殊字符的 `MSGID`、`MSGSTR` 必须使用引号包裹。
- 英文和中文中的 Python 格式化占位符名称必须完全一致，例如都使用 `{name}`。
- `--pair` 与 `--delete` 是互斥模式，一次命令中不得混用。
- 翻译修改后应运行 `src/api/tests/scripts/test_upsert_i18n.py` 和相关 API 测试。
