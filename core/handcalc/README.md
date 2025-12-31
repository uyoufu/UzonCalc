# handcalc 原理介绍

handcalc 的核心思想为：使用 ast 解析，对 python 代码进行插桩，从而根据源码生成一份修改后的代码，然后执行

本模块为源码改写的关键逻辑，分为两个部分，一个是 node_visitor, 一个是 node_handler

可以自行定义 visitor 对源码进行修改，调用对应的 handler 进行转换