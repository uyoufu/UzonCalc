# Bug修复

## 数据库初始值优化

/home/gmx/dev/uzoncalc/src/api/app/db/initializers/default_user.py 优化：
1. 添加默认部门, 用户保存到默认部门中
2. 增加一个非管理员普通用户

## 报告实例

页面 /home/gmx/dev/uzoncalc/src/web/src/pages/calcReportInstance/SharedInstanceDetail.vue 中，通过报告实例分享链接打开时，iframe 中的结果返回 401, 后端应对分享后的结果放行

## 缩略图样式优化

优化缩略图 /home/gmx/dev/uzoncalc/src/core/uzoncalc/cli_core/cli_thumbnail.py 生成效果：

1. 移除顶部的绿色条纹
2. 若有描述，则在标题下方显示
3. python 代码应进行高亮显示
4. /home/gmx/dev/uzoncalc/src/api/app/service/calc_report_archive_service.py render_workspace_archive_thumbnail 在生成缩略图时，应将名称描述传入显示到图片上