---
title: 目录与编号
icon: list-ol
order: 6
---

## 自动目录

调用 `toc()` 可以在当前位置生成目录：

```python
toc("目录")
```

目录会根据文档中的标题层级自动生成，并在导出或打印时计算页码。

## 自动图表编号

使用 `Img()`、`Table()`、`EChart()`、`Plot()` 等函数插入图表时，UzonCalc 会自动维护图号或表号。函数会返回一个编号占位符，可在后续正文中引用：

```python
img_no = Img(
    "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
    alt="UzonCalc 运行结果",
)

f"现在你可以使用 img_no 引用这张图片了：见 {img_no} 所示"
```

最终渲染时，占位符会替换为实际编号，并支持点击跳转到对应图表位置。

## 修改编号前缀

图表编号前缀可以修改：

```python
figure_prefix("Figure")

img_no = Img(
    "https://oss.uzoncloud.com:2234/public/files/images/image-20260527133234259.png",
    alt="UzonCalc 运行结果",
)

f"现在引用图片：如 {img_no} 所示。"

figure_prefix("图")
```

表格编号前缀可使用 `table_prefix("Table")` 设置。前缀设置会影响后续图表，建议在文档开头统一设置。
