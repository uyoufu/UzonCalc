# 项目优化方案

## src/core

1. /home/gmx/dev/uzoncalc/src/core/uzoncalc/template/utils.py load_template 函数调用时，要从环境变量中获取 `<script defer src="https://calc.uzoncloud.com/scripts/template.js"></script>` 中的 src 值，默认值为 `https://calc.uzoncloud.com/scripts/template.js`
2. 需要修改 /home/gmx/dev/uzoncalc/src/core/uzoncalc/template/calc_template.html 以支持 `template.js` 动态设置

## src/web

### 用户信息

1. /home/gmx/dev/uzoncalc/src/web/src/layouts/components/userInfo/userInfo.vue 页面支持多语言
2. 用户信息中的个人信息下面，增加“关于”功能，关于界面中弹出一个弹窗，显示软件的基本信息
3. 若是桌面单机版本(通过 isDesktopApi 判断)，则不显示“退出”功能

### 修改用户信息

1. 重构用户信息页面 /home/gmx/dev/uzoncalc/src/web/src/pages/user/profileIndex.vue，使用 q-tabs、q-tab、q-tab-panels、q-tab-panel 组件实现，每个 tab 对应一个个人信息项，分别为：基本信息、安全设置
2. 在基本信息中，可单击头像进行修改，使用 https://github.com/advanced-cropper/vue-advanced-cropper 优化对用户头像的裁剪功能，当前依赖已经安装
3. 在基本信息中，可修改昵称，需要为用户表新增字段

### 计算报告页面

**计算书分类列表**

1. 计算书分类菜单新增功能：置顶、取消置顶、隐藏，同时支持拖拽排序。拖拽排序使用https://github.com/Alfred-Skyblue/vue-draggable-plus 组件实现，已经安装依赖
2. 计算书分类能自动根据使用频率更新排序，使用 LFU-Aging 算法实现
3. 在“新建分类按钮”左侧新增一个按钮，单击后显示隐藏的分类项，再单击则关闭显示
4. 记录用户上次操作的分类项，下次打开时，自动选中该分类项
5. 固定的分类不可进行拖拽等操作，也不参与排序
6. 新增“共享计算书”固定分类，位于我的收藏之后，共享计算书单击时，右侧改用别外单独的组件显示，详细参考 `### 共享计算书` 中的需求说明

**导入导出**

页面源码位于：/home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/list/CalcReportList.vue

1. 计算报告导入时，支持 .png 和 .uzc 文件格式，.uzc 格式本质为图片，但是在图片末尾添加了源码压缩文件，具体逻辑参考 /home/gmx/dev/uzoncalc/src/core/uzoncalc/cli_core
2. 计算书表格项的右键菜单中，增加“导出”功能，后端将计算书工作空间中所有信息导出为 .png 文件; 要求导出后，能独立执行，所以依赖也需要一并导出
3. 导出时，需要进行权限设置，是否可编辑、可分享；若设置为不可编辑，在导入后，则不允许用户修改任何内容，只能运行；设置不可分享时，则不能再次分享
4. 用户可以通过分享的链接导入计算书，若选择同步，则不能编辑，要与上游保持一致
5. 导入按钮使用 q-fab 组件实现，子组件分别为：文件导入，链接导入

**其它说明：**

导出的内核算法，应首先在 /home/gmx/dev/uzoncalc/src/core/uzoncalc/cli_core 中实现，然后 api 通过代码调用

**分享计算书弹窗**

1. 重新设计整个分享弹窗，让界面美观简洁、交互体验更好
2. 修复分享弹窗中候选版本为空的问题
3. 访问范围修改为：
   - 公开：非登录用户可以通过链接访问
   - 内部：仅登录用户可以通过链接访问
   - 指定用户：指定的用户可以通过链接访问
   - 指定部门：指定的部门可以通过链接访问
4. 允许指定权限：
   - 可编辑：用户导入后，可以修改计算书中的内容
   - 可分享：用户导入后，可以二次分享
5. 用户通过链接导入计算书时，可以选择是否同步，若选择同步，则也不能编辑，要与上游保持一致

### 共享计算书

共享计算书为一个特殊的计算报告分类，用户可以在该分类中查看系统中其它用户共享的计算书。

1. 当用户激活共享计算书分类时，右侧的列表使用单独的组件显示
2. 显示的列分别为：
   - 计算书名称
   - 描述
   - 版本
   - 分享时间
3. 计算书名称列中显示格式为：`{nickName}/{calcCategoryName}/{calcReportName}`
4. 右键菜单有:
   - 导入
   - 导出
5. 导入时，需要选择既有分类，且应选择是否同步
6. 若用户选择了同步设置，下次运行之前，需要先检查是否需要同步新的版本

### CalcReportWorkbench.vue 工作区页面

1. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReport/workbench/CalcReportWorkbench.vue 中除了记录用户的左侧目录树状态外，右侧编辑区的 tag 状态也要记录，在切换或者打开时恢复。这些记录可以保存到本机和服务器，服务器只用作多端同步，恢复时，优先从本机中获取。
2. 目录树中文件，需要增加“复制引用”功能，用于复制该文件的引用路径，不仅包括 .py 文件，还包括 resources 目录的资源文件，可能是图片，excel 等
3. 若是桌面单机版本(通过 isDesktopApi 判断)，在文件和目录上，还需要新增右键功能："在文件资源管理器中显示" 功能，该功能与 vscode 中的作用相同
4. 工作区中各个 .py 文件，应支持相对引用，不与 python 既有编码方式割裂
5. 第一次打开 `运行` 栏时，应自动运行一次，若文件变动，则采用前一次的输入参数，重新运行；若未发生变动，则直接显示上次运行的结果。

### ExecutionPane.vue 运行界面组件

1. 移除 /home/gmx/dev/uzoncalc/src/web/src/pages/calcExecution/components/ExecutionPane.vue 中的 execution-provenance 部分，对于用户来说，并不关心这些系统信息
2. 优化 `silentRun` 的逻辑：静默模式下，不是以默认参数运行，而是遇到 UI 时不中断，从头执行到尾，用户更改参数后，会传入新的参数继续执行。这部分逻辑可以参考 master 分支下的 src/web/src/pages/calcReport/viewer/ 中的实现
3. 打开运行界面时，若存在历史运行记录，要先显示；若不存在，则自动运行。

### 我的计算页面

**实例列表页面**

1. 实例列表页中的数据项右键新增 “分享” 功能，用户可以点击该功能，切换实例的分享切换；
2. 当计算实例分享后，右键中显示 “复制分享链接” 功能，用户可以点击该功能，复制实例的分享链接，分享链接在用户不需要登录，即可访问；计算
3. 实例被分享后，右键新增 “取消分享” 功能，用户可以点击该功能，取消实例的分享

**InstanceDetail.vue 实例详情页面**

1. 实例详情中，若存在参数，也需要支持对参数的修改
2. /home/gmx/dev/uzoncalc/src/web/src/pages/calcReportInstance/InstanceDetail.vue 可以复用 ExecutionPane.vue 组件

### 支持作者页面

将“支持作者页面”重构为支持多语言

### 使用说明页面

1. 使用说明支持多语言
2. 多语言帮助文档位于 /home/gmx/dev/uzoncalc/src/web/public/helps/ 目录下, 格式为 help.{language}.html, 若不存在对应的语言，则显示中文帮助文档。完整的 url path 为: /helps/help.zh-CN.html


## 用户管理

用户管理功能仅在非桌面单机版本、且用户为管理员的情况下显示。

1. 用户管理左侧是部门树、右侧是用户列表
2. 部门树使用 /home/gmx/dev/uzoncalc/src/web/src/components/draggableTree/DraggableTree.vue 来实现，要求可拖拽，右键菜单功能有：
   - 新增同级
   - 新增子级
   - 修改部门
   - 删除部门
3. 当部门树中为空时，菜单项只有“新增部门”，该功能与新增一个顶层的同级部门采用相同的逻辑
4. 要实现功能，后端需要创建部门表
5. 右侧显示用户列表，表头左侧为新增用户按钮，右侧为搜索按钮。
6. 用户列表行上的右键菜单功能有：
   - 禁用用户
   - 启用用户
   - 重置密码

## src/api

1. 根据前端要求，作相应的优化
2. 登录时，在返回的 access 中，需要根据是否存在多个用户，来返回 is_multi_user 权限码，标识是否多用户环境

## 其它说明

在修改上述功能时，可完全重构，根据需求，按最优解实现，不要考虑对既有功能、数据格式的兼容，当前功能处于未公开发布状态，可完全重构