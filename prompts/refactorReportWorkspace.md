# 重构计算报告工作区

1. 将 WorkspacePane 重构为像 vscode 一样，支持多标签页
2. 单击不同文件时，新增不同的标签页面显示
3. `onRunWorkspace` 触发后，直接在新的标签页中显示运行界面，若源码中变动后，切换到运行标签页时，需要能自动同步更改并刷新显示
4. 新增文件后，左侧目录树自动折叠了，需要保持不变
5. 在顶部功能区，新增一个按钮，可以折叠或展开左侧目录树
6. 在目录树目录节点右键时，增加新建文件、新建目录的功能
7. 增加目录树展开状态记忆功能，下次进入时，能保持上次的展开状态和文件选中状态
8. 重写依赖管理界面，使用 LowCode 组件实现

## 关联文件

1. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/workspace/WorkspacePane.vue
2. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/workspace/DependencyDialog.vue