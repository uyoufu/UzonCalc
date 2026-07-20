## 自动生成 ToC 目录

1. 参考 /home/gmx/dev/uzoncalc/src/core/uzoncalc/handcalc/post_handlers 思路，
在 /home/gmx/dev/uzoncalc/src/core/uzoncalc/context_result_handler/ 中实现一个全局的 html 后处理器，接入 /home/gmx/dev/uzoncalc/src/core/uzoncalc/context.py 文件的 html_content 方法中，对 html 内容进行后处理
2. 重构 /home/gmx/dev/uzoncalc/src/core/uzoncalc/template/js/src/toc.ts, 将 toc 的目录生成逻辑变成一个 context_result_handler，当检测到内容中存在 toc 占位符时，则自动生成目录，但不要重复生成，占位内容如下：

参考：/home/gmx/dev/uzoncalc/src/core/uzoncalc/context_utils/doc.py

``` html
<div id="toc" data-toc-title="{safe_title}" style="page-break-before:always;page-break-after:always;">
    <div class="text-center text-2xl font-semibold">{safe_title}</div>
    <div id='toc-container'></div>
</div>
```

3. 移除 /home/gmx/dev/uzoncalc/src/core/uzoncalc/template/js/src/toc.ts 实现，因为已经通过 context_result_handler 实现了目录生成功能