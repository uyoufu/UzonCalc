# 计算查看器

开发 `calcReportViewer` 页面，要求如下：

## 界面 UI

-  q-bar 中间为 q-input 输入框，显示报告名称或者本机的全路径，随后右侧为计算按钮
-  q-splitter before 为报告的 UI 预览区域，after 为计算结果展示区域，结果为 iframe 嵌入

## 功能要求

- 若 `query` 参数中存在 `reportOid`, 获取对应的名称，然后调用后端  `calc_execution.py` 中对应的接口进行计算
- 通过 `query` 参数中的 `silent` 参数控制是否进行逐步计算，逐步计算时，后端会返回一个 executionId, 前端通过该 Id 进行轮询获取计算进度
- 若没有 `reportOid` 参数且输入框中存在路径，则调用 `start_file_execution` 接口进行计算, 且 silent 强制为 true
- 计算 UI 的预览区，使用 `LowCodeForm` 组件进行展示，后端返回的 `ExecutionResult` 中的 `windows` 数组对象与 `LowCodeForm` 组件的 `ILowCodeField` 是兼容的
- 计算结果通过 iframe 嵌入展示，iframe 的 src 通过后端返回的 html 地址进行设置

