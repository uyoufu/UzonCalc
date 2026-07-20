# 更新分享管理器及状态缓存方式

## 分享管理器

1. 完全重构 /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/shared/ShareManagerDialog.vue，使用 flex 布局，Utility-First 风格
2. 复制分享链接按钮应随时可用
3. 移除 linkType 字段，只根据 source 字段判断是否是前端分享链接，当存在 source 时，说明是前端分享链接，否则是后端分享链接
4. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/shared/SharedImport.vue 导入链接若检测到登录用户，则显示导入和下载，否则仅显示下载
5. SharedImport.vue 右侧应是显示上一次该文件执行的结果，若没有结果，则自动运行一次输出，当前始终显示 404, 进行修复

## 状态缓存方式

将 src/web/src/stores 中的状态缓存改为 localStorage，使状态在多个页面之间保持同步