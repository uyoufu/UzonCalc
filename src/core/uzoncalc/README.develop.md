# UzonCalc 核心模块介绍

UzonCalc 的目标是让工程计算书直接用 Python 编写，并自动生成带公式、表格、图形和交互输入能力的 HTML 文档。

## 调用流程

1. 用户用 `@uzon_calc()` 装饰 `async` 计算函数。装饰器位于 `startup.py`，负责识别入口、注入 `ctx` 和 `unit`，并在无上下文时自动创建 `CalcContext`。
2. 首次执行入口函数时，`startup.py` 会调用 `handcalc/ast_instrument.py::instrument_function()` 读取原函数源码，移除装饰器，执行 AST visitor，并生成插桩后的新函数。
3. AST 插桩阶段会把赋值、裸表达式、字符串、f-string 等语句转换为结构化步骤，底层由 `handcalc/ast_to_step.py`、`handcalc/recording_injector.py` 和 `handcalc/steps.py` 协作完成。
4. 函数正式运行后，插入代码会在每个关键语句处调用 `handcalc/recorder.py::record_step()`；运行时的局部变量和值通过 `locals_map` 和 `value` 一并传入步骤对象。
5. 对于公式类步骤，`handcalc/ast_to_ir.py` 先把 Python AST 表达式转换为 `handcalc/ir.py` 中的 MathIR。这里会进一步分派到 `converters/` 处理函数调用、操作符优先级、下标切片、单位表达式等细节。
6. `handcalc/rendering/` 再把 MathIR 与运行时值组合成最终展示内容，包括变量替换、数组样式修正、赋值左右侧拼接、f-string 混排和数值格式化，并输出 MathML 或 HTML 片段。
7. 所有渲染结果最终进入 `CalcContext.append_content()`。如果当前处于 `inline` 模式，会先聚合行内内容；否则直接追加到文档内容列表。
8. `append_content()` 会依次执行 `handcalc/post_handlers/` 中的后处理器，对生成内容做括号简化、符号替换、别名替换、下标规整、URL 格式化等修正。
9. 当用户调用 `ctx.html()`、`ctx.save()` 或 `context_utils/doc.py::save()` 时，`template/utils.py` 会将正文、页面尺寸、页边距、字体、自定义样式和头部资源注入 HTML 模板，生成最终文档。

### 一次典型执行链路

`@uzon_calc async函数` -> `instrument_function()` -> `Ast visitor / RecordingInjector` -> `record_step()` -> `Step.record()` -> `ast_to_ir + converters` -> `rendering` -> `CalcContext.append_content()` -> `post_handlers` -> `template.render_html_template()` -> HTML 文件

## 分层介绍

### 1. 入口层

- `startup.py` 负责创建和切换 `CalcContext`，并提供 `run()`、`run_sync()` 两种执行方式。
- `globals.py` 基于 `ContextVar` 保存当前上下文，供各模块通过 `get_current_instance()` 获取运行现场。
- `cli.py` 用于直接执行计算脚本，并将入口函数输出为 HTML。

### 2. 上下文与文档层

- `context.py` 中的 `CalcContext` 是核心对象，负责保存正文内容、页面选项、默认值、交互状态和缓存句柄。
- `context_options.py` 定义文档标题、页边距、字体、公式替换、f-string 渲染、后处理器等运行选项。
- `context_utils/` 提供开发者直接使用的高层 API：
	- `doc.py` 负责标题、目录、样式、头部资源和保存。
	- `elements.py` 负责段落、标题、表格、图片、代码块、图形等 HTML 片段生成。
	- `options.py` 负责 `hide()`、`show()`、`inline()`、别名、小数精度等行为开关。
	- `ui.py` 负责定义输入窗口，在静默模式下返回默认值，在交互模式下等待前端回填。

### 3. handcalc 计算记录层

- `handcalc/ast_instrument.py` 读取函数源码、移除装饰器、执行 AST visitor、校验并重新编译函数。
- `handcalc/recording_injector.py` 将原始语句改写为 `record_step()` 调用，形成统一记录入口。
- `handcalc/ast_to_ir.py` 和 `handcalc/ast_to_step.py` 负责把 Python AST 转成公式 IR 和结构化步骤。
- `handcalc/steps.py` 定义文本、表达式、赋值、f-string 等记录单元，是运行时真正落地到上下文的执行对象。
- `handcalc/converters/`、`handcalc/rendering/`、`handcalc/post_handlers/` 分别处理“AST 表达式细化”“公式内容渲染”“最终字符串后修正”三层工作。

#### converters

- `converters/` 是 `ast_to_ir.py` 的子分发层，职责是把复杂表达式拆成更细的可维护规则，而不是把所有 AST 逻辑堆在一个文件中。
- `call_rendering.py` 负责普通函数、方法调用、关键字参数和特殊函数格式化，例如把 `sqrt(x)`、`abs(x)` 渲染成更接近数学记号的形式。
- `operator_rendering.py` 负责二元/一元操作符映射和括号判定，保证加减乘除幂在展示时符合优先级和结合律。
- `subscript_rendering.py` 负责变量下标、切片和多维索引的 IR 生成，例如把 `A[i]`、`A[i:j]` 转成 `MSub` 结构。
- `unit_expression.py` 负责识别 `unit.xxx` 参与的乘除幂表达式，把单位部分折叠为统一的单位节点，并尽量分离数值部分。

#### rendering

- `rendering/` 负责把步骤对象和运行时值真正渲染成用户能看到的公式片段。
- `equation_renderer.py` 负责赋值语句、普通表达式、变量替换、数组变量样式、左值修正等核心逻辑，决定公式最终展示成几段。
- `value_renderer.py` 负责把 Python 运行时值转成 MathIR，包括数字、数组、带单位值等，并统一数值格式化精度。
- `fstring_renderer.py` 负责将文本与公式混排，支持在 f-string 中嵌入表达式结果或命名表达式结果。
- `html_renderer.py` 负责根据上下文当前是否处于行内模式，决定包装成 `<p>` 还是 `<span>` 并写回 `CalcContext`。

#### post_handlers

- `post_handlers/` 处理的是“已经渲染出来的字符串内容”，目标不是重新理解 AST，而是修正输出细节。
- `BasePostHandler` 定义统一接口，`priority` 控制执行顺序，`handle(data, ctx)` 允许根据上下文选项调整行为。
- `post_pipeline.py` 负责组装默认处理链，并按优先级排序。
- `parentheses_simplify.py` 用于去除多余括号，`swap_symbol.py` 用于替换展示符号，`swap_alias.py` 用于应用变量别名。
- `script_notation.py` 负责把约定形式的变量名进一步整理为上下标显示，`format_url.py` 负责处理 URL 等文本细节。
- 如果需要新增输出修正规则，应优先新增后处理器，而不是把字符串替换逻辑散落到渲染器或上下文层。

### 4. 输出与扩展层

- `template/` 负责 HTML 模板、样式注入和页面最终渲染。
- `extension/` 提供额外能力，如 Excel 结果转表格、ECharts 图表等。
- `cache/json_db.py` 提供轻量 JSON 缓存，供 Excel 等耗时扩展复用结果。
- `interaction.py` 维护异步输入和结果 Future，是前端交互集成的基础。

## 开发要点

1. 计算入口必须是 `async def`，并使用 `@uzon_calc()` 装饰。
2. 想新增文档能力，优先放在 `context_utils/`，保持用户脚本 API 简单。
3. 想调整公式显示，优先查看 `handcalc/ast_to_ir.py`、`handcalc/rendering/` 和 `handcalc/post_handlers/`。
4. 想新增公式后处理器，可继承 `BasePostHandler`，再加入 `post_pipeline.py` 的默认管道。
5. 想接入外部能力，如表格、图表、第三方计算结果，优先放在 `extension/`，不要污染核心上下文逻辑。
6. 需要持久化轻量结果时，使用 `ctx.get_json_db()`，避免在核心流程中引入更重的存储依赖。

## 本地开发模块安装

在仓库根目录执行：

```bash
uv sync --package uzoncalc --group test
uv run --package uzoncalc --group test pytest tests
```

如只需要核心包运行环境，可执行：

```bash
uv sync --package uzoncalc --no-default-groups
```

## 参考

1. [HandCalc](https://github.com/connorferster/handcalcs/tree/67488b91d1dd5db66c3c8295eea9a01ac496fc20/src/handcalcs)
2. [software_for_hand_calculations](https://www.reddit.com/r/StructuralEngineering/comments/1guxrbn/software_for_hand_calculations/?tl=zh-hans)
