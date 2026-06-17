# 为 uzoncalc 实现 ToC 页码计算

为 uzoncalc 实现 ToC 页码计算功能，功能需求如下：

1. 为 `/home/gmx/dev/uzoncalc/src/api`, `/home/gmx/dev/uzoncalc/src/core/uzoncalc/cli.py` 中添加一个新的接口，向其传递文档链接，后端通过 playwright 服务，打印为 pdf 后，获取每级标题对应的页码信息，返回给前端进行更新
2. /home/gmx/dev/uzoncalc/src/core/uzoncalc/context.py `save()` 被调用时，若存在 toc 占位符，需要自动通过 playwright 获取 toc 中的页码
3. 其它非 html 文件的情况下，即通过 http 在浏览器中打开结果时，在打印按钮回调中，先通过服务请求页码，更新后，再触发系统打印。若链接未变，且页码已经生成，则不再重复请求。

## 要求：

1. 将 playwright 服务在 `src/core/uzoncalc` 中实现，其它地方直接调用，将服务封装为类，这样可在其它地方实现单例模式
2. playwright 参考 /home/gmx/dev/uzoncalc/src/api/app/service/playwright_service.py 这个服务实现，还需要允许设置状态保存位置
3. `/home/gmx/dev/uzoncalc/src/api/app/service/playwright_service.py` 本身应调用 core/uzoncalc 中的 playwright 服务实现

## 其它更新

1. 前端 /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/viewer/CalcReportExecutor.vue 中，当局部内容更新时，还需要向子页面传递更新后的 url, 方便 iframe 中向后端请求 toc 页码信息
