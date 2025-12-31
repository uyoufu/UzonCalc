# UzonCalc

UzonCalc 是一个使用 python 语言来编写工程计算书的软件。

## 实现逻辑

1. 编写 python
2. 调用解析器将源码转换成执行的 python
3. 调用执行的 python

## 特点

1. 支持变量级替换
2. 方便扩展

## 单元测试

在 根目录中执行 `python -m pytest`

**AI 测试**

使用 `conda activate py12` 激活环境后，在根目录中执行 `python -m pytest` 运行测试，若有报错，请修复

## 参考

1. [HandCalc](https://github.com/connorferster/handcalcs/tree/67488b91d1dd5db66c3c8295eea9a01ac496fc20/src/handcalcs)
2. latexify