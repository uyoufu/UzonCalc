# 优化 CalcReportExecutor 渲染效果

优化 CalcReportExecutor 中执行计算后，iframe 的 src 变动导致切换时，渲染有一段空白问题。

## 主要思路

1. 后端在执行计算后，同时对比上一次的计算结果，若仅在 /home/gmx/dev/uzoncalc/src/core/uzoncalc/template/calc_template.html 中的 CONTENT_START_MARK 到 CONTENT_END_MARK 之间有变化，则同时返回变化内容
2. 前端将内容通过 postMessage 发送至 iframe 内部，iframe 内部根据 CONTENT_START_MARK 到 CONTENT_END_MARK 之间的内容更新 iframe 内容
3. iframe 内部更新后，需要重新走一次初始化逻辑

## src/web 前端

核心逻辑位于：/home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/viewer/CalcReportExecutor.vue

## src/api 后端

1. /home/gmx/dev/uzoncalc/src/api/app/controller/calc/calc_execution.py 在 start_calc_execution 函数的 body 中同时获取 `lastHtmlPath` 字段，用于对比两次结果