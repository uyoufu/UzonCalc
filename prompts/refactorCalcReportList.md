# 重构 CalcReportList 组件

按以下要求重构或优化：

1. 计算书分类 `ReportCategoryPanel.vue` 中，增加我的收藏固定分类，位于分类列表的顶部，用于显示用户收藏的计算书分类。
2. 版本管理 `VersionPane.vue` 中的发布版本功能迁移到计算书列表中的右键菜单中，仅存在"有未发布修改"时才显示发布版本选项。
3. 版本管理界面、运行界面，在任何大小的窗口都显示，仅 CalcReportWorkbench 组件中需要验证是否是桌面端，验证桌面端改用 `Platform.is.desktop` 验证
4. 由于版本管理、运行界面已经被当做独立的路由，因此重构其目录结构，版本管理重构到 `/home/gmx/dev/uzoncalc/src/web/src/pages/calcReport` 目录下，`ExecutionPane.vue` 重构到  /home/gmx/dev/uzoncalc/src/web/src/pages 目录下，并对两者文件或者目录名进行合适的命名优化
5. ReportTable.vue 中，将“运行最新版本”改为运行，允许运行未发布版本的报
6. 从 ReportTable.vue 右键进入路由之前，提前在 query 中添加 tagName 参数，用于区别不同的 report

## 关联文件

1. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/list/CalcReportList.vue
2. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/list/components/ReportCategoryPanel.vue
3. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/version/VersionPane.vue
4. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/execution/ExecutionPane.vue
5. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/CalcReportWorkbench.vue
6. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/list/components/ReportTable.vue