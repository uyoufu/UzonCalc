# 重构计算报告源码保存方式

- 参考方案 /home/gmx/dev/uzoncalc/src/api/refactorPlan.md 使用项目 `oid` 和 `workspace` 目录保存当前内容，解除展示名称和分类对文件路径的影响。
- 目前仅实现本机沙箱环境，后缀再实现 docker 环境

## 相关文件或目录

1. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport
2. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReportInstance
3. /home/gmx/dev/uzoncalc/src/web/src/pages/dashboard


## 其它说明

不考虑数据兼容问题，可完全重构