# 为 uzoncalc 实现 ToC 页码计算

为 uzoncalc 实现 ToC 页码计算功能，功能需求如下：

1. 为 `/home/gmx/dev/uzoncalc/src/api`, `/home/gmx/dev/uzoncalc/src/core/uzoncalc/cli.py` 中添加一个新的接口，向其传递文档链接，后端通过 playwright 服务，打印为 pdf 后，获取每级标题对应的页码信息，返回给前端进行更新
2. 
