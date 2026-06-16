# 自动生成分页编号

为 uzoncalc 添加自动生成编号功能， 要求如下：

1. 使用 src/api/app/service/playwright_service.py 创建一个新服务用于返回每级标题打印为PDF后所在的页码
2. 移除 /home/gmx/dev/uzoncalc/src/core/uzoncalc/template/js/src/pagination.ts 逻辑，页码只用空白占位符标记，方便用户自行打印后，可以手动添加页码
3. 优化打印按钮逻辑，若打印时，非本机文件，则从后端中获取
