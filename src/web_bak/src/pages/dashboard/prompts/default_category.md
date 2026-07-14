为 DashboardIndex.vue 在 onMounted 中获取一个默认的分类 oid，在请求时，向服务器传递 defaultCategoryName，若后端用户中不存在任何有效分类，则使用默认名称创建一个分类后返回
前端接口应保存到 `src/api/calcReportCategory.ts` 中
