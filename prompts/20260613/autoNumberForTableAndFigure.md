# 实现图表自动编号

为 uzoncalc 实现图表自动编号的功能：

1. `Table` 和 `Img`、 `EChart`、`Plot` 等图表元函数在调用时，需要返回一个标签占位符，如 `<span id='table-1'></span>`, 该占位符可以持续文档中使用, 占位符中的唯一序列数字通过 get_serial_number 方法获取
2. 在渲染后，根据标签占位符，自动生成图表编号，如 `图 1.1`、`图1.2` 等，这部分逻辑在 src/core/uzoncalc/template/js/src 中增加独立的 js 文件来实现

## 相关文件

src/core/uzoncalc/context_utils/table.py
src/core/uzoncalc/context_utils/elements.py
