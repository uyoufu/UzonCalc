# UzonCalc

UzonCalc 是一个使用 python 语言来编写工程计算书的软件。

## 实现逻辑

1. 用户编写 python 源码
2. 软件通过 AST 分析，向源码中插桩输出代码，编译为新的代码
3. 执行新编译的代码

## 特性

1. 支持变量级替换
2. 方便扩展

## 使用 matplotlib

可以通过

## 单元测试

在 根目录中执行 `python -m pytest`

**AI 测试**

使用 `conda activate py12` 激活环境后，在根目录中执行 `python -m pytest` 运行测试，若有报错，请修复

## 参考

1. [HandCalc](https://github.com/connorferster/handcalcs/tree/67488b91d1dd5db66c3c8295eea9a01ac496fc20/src/handcalcs)
2. [software_for_hand_calculations](https://www.reddit.com/r/StructuralEngineering/comments/1guxrbn/software_for_hand_calculations/?tl=zh-hans)