# 优化源码保存逻辑

## 工作区

1. 工作区右侧区域顶部的导航栏增加右键菜单，与 vscode 中的表现一致，包含：
  - 关闭
  - 关闭其它
  - 全部关闭
  - 复制引用

2. 将工作空间根目录当成一个包，不再区分 src 目录和 resources 目录, 同时移除 resources 目录，所有目录都可以上传资源；初始化时，直接在根目录下创建 main.py 文件作为入口文件
3. 同时优化 /home/gmx/dev/uzoncalc/src/core/uzoncalc/cli_core zip 逻辑，根据入口文件所在的目录为工作区根目录进行打包，需要解析绝对路径和相对路径导入的外部资源，仅限工作区内

**复制引用**

复制引用时，应相对于工作区根目录计算，不再根据 src 进行计算

## 相关文件

1. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/CalcReportWorkbench.vue

## 其它

不考虑兼容性，以最优的方式优化