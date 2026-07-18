# 页面与分享体系优化完整技术方案

## 1. 总体目标

本方案是 `prompts/optimizePages.md` 的实施依据。采用不兼容重构，不保留旧数据库格式、审核接口或旧页面逻辑；继续沿用现有 CalcReport 多文件 workspace、不可变 version、artifact/bundle 执行体系。

## 2. 核心决策

- 删除版本审核字段、接口和页面，所有已发布版本均可直接分享。
- 报告来源统一为 `native`、`copy`、`share_import`、`share_sync`、`file_import`，列表展示来源及同步状态。
- `canEdit`、`canShare` 只在 UzonCalc 数据库和业务接口层执行，不加密或混淆源码；派生复制不得放宽原权限。
- 同步报告只读，本地缓存上游不可变版本；发现更新时列表提示，运行前询问，拒绝更新时允许继续运行当前缓存版本。
- 用户与部门为多对多关系；部门分享授权覆盖所选部门及其所有后代部门。
- 只有公开链接允许跨后端导入；内部、指定用户、指定部门仅支持同一后端。
- 固定分类顺序为“我的收藏、共享计算书、全部计算书”，不可拖拽、隐藏、置顶或参与 LFU。
- 用户置顶分类使用手工拖拽排序；未置顶分类使用 LFU-Aging；拖入置顶区即置顶，取消置顶后恢复自动排序。

## 3. 数据模型

| 模型 | 关键调整 |
| --- | --- |
| `users` | 将模糊的 `name` 改为 `nickName`；登录和用户 DTO 统一该字段 |
| `department` | `oid/name/parentId/sortOrder/deletedAt`，限制同级重名、循环移动及非空删除 |
| `department_user` | 用户与部门多对多关联，组合主键 |
| `calc_report_category` | 增加 `isPinned/isHidden/manualOrder/frequencyCount/agingEpoch/lastUsedAt` |
| `calc_report` | 增加 `originType/canEdit/canShare/isSystemComponent`；只读来源不得保存 workspace |
| `calc_report_origin` | 保存来源报告、版本、归档 hash 和来源 metadata |
| `calc_report_sync_source` | 保存加密的上游 locator、远程报告标识、当前版本/hash、检查与同步时间 |
| `calc_report_share_link` | 改为报告和版本来源、四种访问范围、`canEdit/canShare`、撤销和有效期 |
| 分享接收者 | 保留用户关联并新增部门关联；删除审核相关约束 |
| `user_input_history` | 增加最近一次 UI window schema，使历史结果和实例可恢复参数界面 |
| `calc_report_instance` | 增加 `inputWindows`；实例分享使用独立可撤销分享记录 |
| 分享预览执行 | 记录分享专属默认参数执行结果，禁止复用作者的私人输入历史 |

LFU-Aging 使用七天 aging epoch。分类被访问时，先按跨越 epoch 数对全部未置顶、未隐藏分类执行右移衰减，再对当前分类计数加一；排序按计数、最近使用时间和稳定 ID 依次比较。

## 4. Core 与归档格式

- `load_template()` 使用环境变量 `UZONCALC_TEMPLATE_SCRIPT_SRC`，默认 `https://calc.uzoncloud.com/scripts/template.js`；缓存原始模板，每次渲染注入经过 HTML 转义和 HTTP(S) 校验的地址。
- 将 `cli_png_container` 扩展为统一读写器，定义 v3 PNG 私有块归档；`.png` 与 `.uzc` 仅是扩展名差异，导入按 PNG 签名、私有块和 manifest 识别。
- v3 归档包含根 workspace、资源、CalcReport 依赖闭包、依赖图、启动器、来源信息和 `canEdit/canShare` 策略。
- API 必须调用 core 的打包、读取和校验函数，不复制 ZIP/PNG 解析逻辑。
- “独立执行”定义为无需源服务器、且报告本地模块、资源和 CalcReport 依赖完整；仍要求安装兼容的 Python 与 UzonCalc 运行时。
- 校验路径穿越、符号链接、重复文件、CRC、manifest/hash、文件数、单文件大小、解压总大小和压缩炸弹。

## 5. API 与权限合约

- 用户接口改为当前用户语义：`GET/PUT /user/me`、头像、修改密码；登录 `access` 动态追加 `is_multi_user`，管理员身份来自角色而非用户名。
- 管理接口提供部门树 CRUD/移动，以及用户 `/count`、`/items`、创建、启用、禁用、重置密码；统一要求非桌面部署和管理员角色。
- 分类接口增加 `pin/hide/access/order` 操作；列表返回固定分组所需状态，最后选择通过本地设置和 `user_settings` 双写，本地优先恢复。
- 导入统一为 `/calc-report/imports/archive` 和 `/calc-report/imports/link`；导出使用流式 `.png` 响应并通过 `notifyUntil` 展示进度。
- 分享范围改为 `public/internal/specified_users/specified_departments`；所有发布版本均为候选，权限默认关闭。
- 可用共享列表采用 `/count` 与 `/items`，复用 `PaginationDTO`；名称返回 `{nickName}/{categoryName}/{reportName}`。
- 同步接口返回 `current/update_available/source_unavailable/access_revoked`，同步时先暂存完整依赖闭包，校验成功后原子切换本地 latest。
- 生成的前端链接使用 `linkType=frontend&source=<base64url(backendShareUrl)>`；`linkType=backend` 或缺少标识时按后端地址解析。
- 远程地址仅允许公开分享，并执行 HTTPS、DNS/private-IP、重定向次数、响应大小和允许主机策略，防止 SSRF。
- 公开分享页允许匿名读取基本信息和只读运行固定版本；没有分享专属结果时，用真实默认参数静默生成，匿名用户不能修改参数。
- 实例分享提供创建、复制链接、撤销及匿名读取接口；结果资源通过分享 token 校验，不直接暴露任意文件路径。

## 6. 前端方案

- 用户菜单全部国际化，在“个人信息”下增加“关于”；关于弹窗显示产品、客户端/API 版本、作者和项目地址；`isDesktopApi` 时隐藏退出。
- 个人信息页改为“基本信息/安全设置”tabs；基本信息支持昵称和头像，裁剪器切换到 `vue-advanced-cropper`，移除未再使用的 `vue-cropper`。
- 分类面板使用 `vue-draggable-plus`，提供隐藏项切换、置顶区、LFU 区和独立共享分类；共享分类右侧使用专用 `SharedReportList`。
- 导入按钮改为 `q-fab`，包含文件导入和链接导入；导入不可编辑链接时，必须确认无法在应用内审查源码的执行风险。
- 分享弹窗继续使用 `ShareManagerDialog` 和组件弹窗封装，分为版本、范围、接收者、权限和现有链接区域，候选版本不再按审核状态过滤。
- 工作区视图状态扩展为目录展开、选中文件、tab 顺序、活动 tab 和树显隐；本地立即保存，服务器防抖同步，本地记录优先。
- 文件树增加“复制引用”和桌面端“在文件资源管理器中显示”；传递规范化 workspace 相对路径并由后端再次校验。
- worker 以模块方式运行入口并配置 workspace root/`src` 搜索路径，支持标准 Python 相对导入。
- `ExecutionPane` 删除 provenance；静默模式完整执行，参数修改后重新启动完整执行；交互模式才暂停并调用 continue。
- 工作区首次打开运行 tab 时：同 artifact 有历史结果则直接恢复，源码变化则沿用匹配字段的前次输入重新运行，无历史则自动运行。
- 独立运行页优先展示历史结果，无历史才自动运行；实例详情复用 `ExecutionPane` 并从 `inputWindows/defaults/resultPath` 恢复可编辑参数。
- 实例列表右键按分享状态显示“分享、复制分享链接、取消分享”；匿名实例页只读。
- 支持作者页面和所有新增文案通过 `i18n:upsert` 维护；帮助页加载 `/helps/help.{locale}.html`，文件缺失或语言不支持时回退中文。
- 用户管理页使用 `DraggableTree` 和 `useQTable`，部门为空时仅显示新增部门，用户表支持搜索、创建、启停和重置密码。

## 7. 实施顺序

1. 完成 core 模板注入、v3 归档读写与安全测试。
2. 重构 ORM、枚举和 DTO，删除审核体系，重新生成单一初始 Alembic 迁移。
3. 实现用户、部门、分类 LFU、来源和权限服务。
4. 实现本地/远程分享协议、归档导入导出、同步及匿名预览执行。
5. 重构执行历史、silent 模式、相对导入、实例参数和实例分享。
6. 完成用户资料、分类/共享、工作区、运行、实例、帮助及管理页面。
7. 使用脚本批量维护中英文文案，删除失效依赖、审核组件和旧接口。
8. 按需求逐项执行回归、跨后端、桌面和响应式验收。

## 8. 测试与验收

- Core 覆盖模板默认值/环境变量、PNG round-trip、双扩展名、资源和依赖闭包、独立执行及恶意归档。
- API 覆盖多部门授权、管理员限制、LFU 衰减、权限继承、四种分享范围、同步原子性、远程公开限制和 SSRF。
- 执行测试覆盖静默/交互分流、历史恢复、源码变更重跑、默认参数公开预览及三种 sandbox 的相对导入。
- 前端 Vitest 覆盖分类拖拽、FAB 导入、分享弹窗、状态恢复、ExecutionPane、实例菜单、资料 tabs 和路由权限。
- Cypress 覆盖匿名分享运行、匿名实例查看、同步确认、不可编辑风险提示、部门用户管理及桌面/移动布局。
- 运行 core/API 聚焦 pytest、迁移测试、`bun run lint`、`vue-tsc --noEmit`、`bun run test:unit:ci` 和 `bun run build`。
- 验收要求每条需求均有对应测试或人工场景记录，不允许仅以构建成功代替业务验证。

## 9. 默认与边界

- 当前功能未发布，不提供旧数据、旧 API、旧审核状态或旧归档格式的兼容迁移。
- 删除现有迁移后，按 `src/api/app/db/migration/README.md` 从空数据库使用 `revision --autogenerate` 生成新基线并人工检查 SQLite/PostgreSQL DDL。
- 同步更新被拒绝时运行当前本地缓存版本；分享撤销只阻止后续同步，不删除已合法导入的缓存版本。
- 固定分类不落库；隐藏分类只在显式显示隐藏项时出现，不参与 LFU。
- 归档权限属于应用内策略，不承诺阻止外部工具提取或修改可独立执行的源码。
