# 路由开发文档

## 路由缓存

- 路由默认缓存，若要取消缓存，在 meta 中设置 noCache: true，并且在组件中使用 defineOptions 定义 name 属性，name 要与文件名一致
- 缓存通过 route.fullPath 和 route.query 生成 id 来实现，若同一个组件，不同页面需要不同的缓存，则需要在 query 中添加一个唯一的参数 random
- 若要向路由标签中添加后缀名，可以在 query 中添加一个 tagName 参数，标签页会优先使用 tagName 作为标签名称
- 也可以在 query 中添加一个 `__cacheKey` 参数，来覆盖默认的缓存 key 生成逻辑
