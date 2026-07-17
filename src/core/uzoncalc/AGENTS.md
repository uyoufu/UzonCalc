# src/core/uzoncalc 开发约束

## 基本边界

- 这里是 `uzoncalc` 核心 Python 包；核心运行依赖只添加到 `src/core/pyproject.toml`，不要加到根目录 `pyproject.toml`。
- 根目录 `pyproject.toml` 只管理 uv workspace 和根级开发工具依赖。
- 修改 `template/js` 前必须先读取 `src/core/uzoncalc/template/js/AGENTS.md`，该目录使用 Bun 工具链。

## 常用命令

在仓库根目录准备核心包测试环境：

```bash
uv sync --package uzoncalc --group test
```

运行核心测试时优先使用目标测试文件或目标用例：

```bash
uv run --package uzoncalc --group test pytest tests/<test_file>.py -q
```

核心测试统一从已安装的发布包名 `uzoncalc` 导入，不使用 `core.uzoncalc`、
`PYTHONPATH=src` 或测试内 `sys.path` 注入。

修改 `template/js` 后在 `src/core/uzoncalc/template/js` 下运行：

```bash
bun test
bun run build
```

## 实现入口选择

- 新增面向用户脚本的文档能力，优先放在 `context_utils/`，保持用户 API 简洁。
- 调整公式 AST 到数学结构的转换，优先查看 `handcalc/ast_to_ir.py` 和 `handcalc/converters/`。
- 调整公式 HTML/MathML 展示，优先查看 `handcalc/rendering/`。
- 调整已经生成的字符串细节，优先新增或修改 `handcalc/post_handlers/`，不要把零散字符串替换塞进上下文层。
- 调整整篇 HTML 输出结果，优先放在 `context_result_handler/`，不要回退到模板前端重复生成。
- 外部能力集成优先放在 `extension/`，避免污染 `CalcContext` 主流程。

## 测试放置

- 核心包相关测试放在根目录 `tests/` 下。
- 模板 JS 测试放在 `src/core/uzoncalc/template/js/src/` 附近的现有测试结构中。
