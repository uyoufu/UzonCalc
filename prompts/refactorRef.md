# 优化工作区逻辑

1. 工作区右侧区域顶部的导航栏增加右键菜单，与 vscode 中的表现一致，至少包含：
  - 关闭
  - 关闭其它
  - 全部关闭
  - 复制引用

2. 工作区的 src 目录应是一个包, 在运行时, src 下的文件可以相对于 src 目录进行引用
3. src 目录中，允许存放任意类型的文件，也允许上传资源到任意目录中
4. 移除 resources 目录
5. 用户可能直接通过 vscode 编辑源码，在工作区中需要能够同步本机的文件更新

## 相关文件

1. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/CalcReportWorkbench.vue

## 其它

不考虑兼容性，以最优的方式优化工作区逻辑