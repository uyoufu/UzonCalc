# HTML 结果缓存

在 `html_cacher.py` 中实现一个 HTML 结果缓存服务，负责对 calc_execution_service 中 ExecutionResult 的 HTML 结果进行缓存，要求如下：

1. 将 html 缓存到 `data/public/calcs/user_id/execution_id/contentHash.html` 文件中, 其中 user_id 为用户 ID，execution_id 为计算执行 ID，contentHash 为 HTML 内容的 hash 值
2. 对于 html 中的 base64 图片，需要将其缓存到同级目录下的 `images/` 目录中，并将 html 中的 base64 图片引用替换为相对路径引用
3. 然后返回缓存后的 html 路径 `public/calcs/user_id/execution_id/contentHash.html`，供前端加载使用
4. 对于缓存目录 `data/public/calcs/user_id/execution_id/`，使用 `create_tmp_file` 方法创建临时文件，过期时间为 1 小时
