# handcalc 原理介绍

handcalc 的核心思想为：使用 ast 解析，对 python 代码进行插桩，从而根据源码生成一份修改后的代码，然后执行

本模块为源码插桩的核心实现，步骤为：

1. 入口位于 ast_instrument.py 的 `instrument_function` 中
2. 调用 ast_visitor 中的 `AstNodeVisitor` 对 ast 进行转换
3. AstNodeVisitor 中调用不同的 recorders 将不同的语句进行插桩
4. recorders 通过调用 token_handlers 来解析每个 ast 节点，并解析为输出结果
5. 当结果生成后，调用后处理管道对字符串进行后处理