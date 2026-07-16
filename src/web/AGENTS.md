# 仓库指导

## 项目结构与模块组织

这是 UzonCalc 前端项目，基于 Quasar、Vue 3、TypeScript 和 Bun 构建。

**目录结构**

应用代码位于 `src/` 下，包含以下模块：

- `api/` 存放 HTTP 客户端
- `boot/` 初始化应用服务
- `components/` 存放跨页面或全局复用的 UI
- `compositions/` 存放跨页面或全局复用的 Vue 3 组合式 API
- `layouts/` 定义页面外壳
- `pages/` 存放路由级页面，页面私有组件和 composable 默认随页面放置
- `router/` 管理导航
- `stores/` 存放 Pinia 状态
- `utils/` 存放共享工具
- `public/` 存放静态资源
- `assets/` 存放源码资源，如图片、字体等
- `tests/` 存放测试代码
- `tests/vitest/` 存放 Vitest 测试代码
- `tests/cypress/` 存放 Cypress 端到端测试代码
- `tests/components/` 存放组件测试规格

**模块组织**

- 路由级页面按路由层级组织目录结构，保存到 `src/pages/` 目录下
- 子目录使用 camelCase 命名风格; 入口组件为 `${PageName}Index.vue`, 使用 PascalCase 命名
- 页面内组件和 composable 放到对应页面目录下, components 目录还可以嵌套存在 components 和 compositions 目录
- 仅与具体业务无关的公共组件和全局复用的 composable，放到 `src/components/` 和 `src/compositions/` 目录中
- 页面入口组件中，不包含具体业务逻辑，仅对所有的组件和 composable 进行初始化和聚合
- 页面中不使用 q-page 作为根元素，已经在 layout 中使用了 q-page

## 组件设计

- 将视图拆分为职责聚焦的子组件，每个组件只负责一个清晰关注点
- 保持组件之间低耦合
- 同类逻辑重复出现两次及以上时，提取为工具函数或 composable
- 若单个组件的职责多于 3 个时，应将其拆分为多个 composable
- 页面中的右键菜单应在单独的 composable 中实现

## 组件复用

1. 通用表格展示先读取 src/components/tableComponents/README.md，再以 src/components/tableComponents/tableExample.vue 为初始化模板，复用 src/compositions/qTableUtils
2. 右键菜单组件，读取 src/components/contextMenu/README.md 使用说明进行复用
3. 若要使用弹窗，读取 src/components/lowCode/README.md 使用说明进行复用
4. 对于按钮，优先复用 `src/web/src/components/quasarWrapper/buttons/` 下实际存在的语义按钮组件；没有合适的语义按钮时使用 `CommonBtn`，不要在页面中直接新增 `q-btn`。
5. 将既有 `q-btn` 重构为 `CommonBtn` 时，若按钮内包含 `q-tooltip`，删除嵌套的 `q-tooltip`，并将提示内容通过 `CommonBtn` 的 `:tooltip` 属性传入。
6. `src/web/src/components/quasarWrapper/buttons/` 下的按钮组件已自动注册，在模板中直接使用，不需要手动导入。
7. `src/web/src/pages/login/loginIndex.vue` 中的登录按钮是保留原 `q-btn` 实现的明确例外。

## 数据请求与更新

1. 不要在 OnMounted 中请求所有数据，而是按需获取
2. 对于仅按钮、右键菜单回调时才需要的数据，在对应事件处理函数中请求
3. 当表格中只有一个数据项变化时，不要刷新整个表格，优先使用 `useQTable` 返回的 `addNewRow`、`updateExistOne`、`deleteRowById` 更新本地行

## 弹窗与反馈

弹窗的详细使用见文档 `src/components/lowCode/README.md`

- 表单弹窗优先使用 `src/components/lowCode`
- 长耗时操作使用 `notifyUntil` 包裹，以提供执行进度反馈
- 优先使用 `src/utils/dialog.ts` 中的提示工具，尤其是 `notifySuccess`、`notifyError`、`notifyWarning` 和 `confirmOperation`
- 需要原生 q-dialog 的复杂交互时, 使用 `src/components/quasarWrapper/PopupDialogExample.vue` 模板定义成页面私有组件，然后在独立的composable 组件中调用 `showComponentDialog` 函数显示弹窗。

## 组合式 API

- 按功能组织独立 composable，例如 `useSaveXxx`、`useDialogXxx` 或 `useTableXxx`
- 每个 composable 只聚焦一个职责
- 将相关状态和处理函数放在一起，例如 `onSaveXxx`、`isSaving`、`canSaveXxx`
- 解构 `const { xxx } = useXxx()` 时，暴露字段应保持精简；超过约 10 个字段时，优先拆分 composable，而不是包装返回值
- 为了保持调用链清晰，不要将函数通过对象的方式间接传入其它接口，可以直接传入

## 命名

- 布尔状态使用 `is`、`can` 或 `has` 前缀
- 组件事件和动作处理函数使用 `on` 前缀
- 命名应直接表达意图，方便项目级检索

## 样式

- 总体风格为卡片式、响应式、无边框的视觉设计
- 优先使用 Quasar 工具类，例如 `text-subtitle1`、`text-primary`、`row`、`col`
- Tailwind 可用于新增布局、间距、响应式和小范围样式补充，存量页面保持现有 Quasar 优先的风格
- 添加自定义样式前，先保持与现有视觉语言一致

## Vue 自动引入

前端在 `quasar.config.ts` 中通过 `unplugin-auto-import/vite` 自动引入 `vue`、`vue-router`、`pinia` 和 `quasar` 的常用 API。在 `.vue` 和 TypeScript 代码中使用这些来源的函数时，不需要再手动添加 import，例如 `ref`、`computed`、`watch`、`onMounted`、`useRouter`、`useRoute`、`defineStore`、`useQuasar` 等。

组件按需引入由 `unplugin-vue-components/vite` 负责，并配置了 `ElementPlusResolver()` 和 `QuasarResolver()`。在 Vue 模板中使用 Element Plus 或 Quasar 组件时，不需要手动导入组件，例如 `<ElButton>`、`<ElForm>`、`<QBtn>`、`<QTable>` 等。

项目本地组件、业务 composable、工具函数、API 方法和 store 实例仍应按实际路径显式导入，除非已在 `quasar.config.ts` 中加入对应的自动导入规则。

## 国际化与多语言

- 多语言字段名按模块、页面、组件组织，例如 `loginPage.title`、`routes.title`、`components.tableExample.title` 等。
- 禁止读取、编辑 `src/i18n/locales/` 目录下的文件，新增、更新、删除多语言字段应使用 `scripts/upsert_i18n.js` 脚本完成
- 单条更新：`bun run i18n:upsert -- --key loginPage.title --zh-CN "标题" --en-US "Title"`
- 批量更新： `bun run i18n:upsert -- --pair loginPage.title "标题" "Title" --pair loginPage.subtitle "副标题" "Subtitle"`，每个 `--pair` 的参数顺序固定为 key、中文、英文
- 批量删除：`bun run i18n:upsert -- --delete loginPage.title --delete loginPage.subtitle`，不存在的 key 会被忽略，`--delete` 不与新增或更新参数混用
- 对于 q-table 中的 columns 定义，使用 computed 函数返回，以支持多语言切换

## 构建、测试与开发命令

- `bun install`：使用固定的 Bun 包管理器安装依赖。
- `bun run dev`：启动 Quasar 开发服务器。
- `bun run build`：使用 `quasar build` 构建生产版本。
- `bun run lint`：对 `.js`、`.ts` 和 `.vue` 文件运行 ESLint。
- `bun run test:unit`：以监听模式运行 Vitest。
- `bun run test:unit:ci`：为 CI 单次运行 Vitest。
- `bun run test:e2e:ci`：启动应用并运行 Cypress 端到端测试。
- `bun run test:component:ci`：运行 Cypress 组件测试。

## 代码风格与命名约定

遵循现有 Vue 单文件组件和 TypeScript 风格。Prettier 配置为不使用分号、使用单引号、`printWidth: 120`、不使用尾随逗号，并为箭头函数参数添加括号。ESLint 强制执行 Vue、Quasar 和 TypeScript 推荐规则，包括 TypeScript 类型使用 type-only import。文件、函数和 ref 使用描述性业务命名；布尔值优先使用 `is*`、`has*` 或 `should*`，事件回调使用 `on*`，例如 `onCancelClick`。

## 测试规范

单元测试使用 Vitest，端到端或组件行为测试使用 Cypress。Vitest 匹配 `src/**/*.vitest.{test,spec}.*` 和 `test/vitest/__tests__/**/*.{test,spec}.*`。Cypress 规格文件使用 `.cy.ts`。行为变更需要新增或更新聚焦的回归测试，并将 fixture 和 support 代码放在对应的 `test/cypress/` 或 `test/vitest/` 区域。

## 提交与 Pull Request 规范

近期提交历史使用简短的祈使句主题，并带有 `feat:`、`refactor:`、`Docs:`、`Build:`、`Chore:` 等前缀。保持提交聚焦，必要时说明受影响的模块。Pull Request 应包含简洁的变更摘要、关联 issue 或任务、测试结果，以及可见 UI 变更的截图或录屏。

## 配置与安全说明

运行时配置示例位于 `public/app.config.json` 和 `src/config/`。不要提交密钥、令牌或特定环境凭据。API 和 SignalR 变更在合并前应与后端契约保持一致。
