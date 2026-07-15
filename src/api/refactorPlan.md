# CalcReport 存储、版本、预插桩与沙箱执行重构方案

## 1. 背景与目标

当前计算书由数据库记录和单个 Python 文件组成，源码路径由用户、分类和名称共同决定：

```text
data/calcs/{userId}/{categoryName}/{reportName}.py
```

该模型无法稳定支持多文件计算书、跨计算书引用、不可变版本、分享导入和隔离执行。名称或分类变化会移动源码，辅助模块无法可靠参与缓存失效，主 API 和 sandbox 之间还依赖宿主机路径。

重构后的 `CalcReport` 应同时满足：

1. 使用 `reportOid` 作为稳定身份，展示名称、分类和物理路径互不耦合。
2. 一个计算书可以包含入口脚本、辅助模块和资源文件。
3. 当前编辑内容、已发布版本和 latest 指针职责明确。
4. 仅已发布版本可以被其他计算书引用、分享或正式执行。
5. 同一次执行可以引用同一计算书的多个发布版本。
6. 所有执行都固定到可复现的源码、依赖、预插桩产物和运行时版本。
7. 本机 sandbox 与 Docker sandbox 使用相同 bundle 协议和缓存键。
8. 托管计算书在首次执行时按 runtime fingerprint 懒构建插桩文件，后续执行复用 READY 产物。

本方案统一使用 `CalcReport` 领域命名。

## 2. 核心概念

### 2.1 身份、名称与路径分离

| 概念 | 示例 | 职责 |
| --- | --- | --- |
| 报告 OID | `67ab...` | API、权限和物理存储的稳定身份 |
| 展示名称 | `连续梁承载力计算` | UI 展示，可修改 |
| workspace revision | `18` | 当前工作区的并发保存边界 |
| 源码 artifact hash | `sha256:source...` | 完整源码和资源快照 |
| 执行 artifact hash | `sha256:exec...` | 特定工具链生成的预插桩文件 |
| 发布版本 | `1.2.1` | 不可变源码 artifact 的语义版本 |
| 依赖别名 | `continuous_beam` | 当前计算书源码中的局部引用名 |
| bundle hash | `sha256:bundle...` | 一次确定的入口、依赖和运行时组合 |

展示名称和分类不参与源码路径、Python 模块名或缓存键。所有物理路径均由服务端根据 OID 或内容 hash 推导。

### 2.2 workspace、version 与 latest

```text
workspace
  当前可编辑内容，可以反复保存

published version
  绑定一次不可变源码 artifact，不允许覆盖

latest
  指向某个 published version 的数据库指针
```

- 保存只更新 workspace，不自动发布，也不改变 latest。
- 发布创建新的 `MAJOR.MINOR.PATCH` 版本，并默认将 latest 指向该版本。
- latest 可以回退到任意已有版本，不修改 workspace。
- 从旧版本恢复只替换 workspace，不修改 latest。
- `latestVersionId` 是唯一权威来源；`latest.json` 只是可重建投影。
- workspace 可以在编辑器中预览执行，但不能成为其他报告的依赖或分享来源。

## 3. 文件与 artifact 存储

### 3.1 报告工作区

```text
data/calc-reports/{userId}/{reportOid}/
  workspace/
    calcbook.json
    src/
      main.py
      api.py
      helpers.py
    resources/
  latest.json
  version/
    v_1_2_1/
      calcbook.json
      src/
      resources/
```

约定：

- 默认入口为 `src/main.py`，实际入口由 `calcbook.json.entryPath` 声明。
- `src/api.py` 或清单中的 export modules 用于跨计算书复用。
- 其他报告不得直接引用目标报告的 `main.py`，避免触发入口初始化。
- 资源只能通过计算书根目录内的规范化相对路径访问。
- workspace 和 version 目录用于编辑、人工检查和恢复，不直接暴露给执行进程。

### 3.2 内容寻址存储

```text
data/calc-artifacts/sha256/{prefix}/{artifactHash}/
  manifest.json
  payload.zip
```

artifact 分为：

```text
SOURCE
  用户源码、资源、calcbook.json 和依赖声明快照

INSTRUMENTED
  由 SOURCE 和 toolchain fingerprint 派生的预插桩 Python 文件及 source map
```

SOURCE 是可编辑、发布、分享和导出的权威内容，并为执行提供资源文件。INSTRUMENTED 是可删除、可重建的代码缓存，不复制资源，不得覆盖用户源码，也不得作为分享来源。

artifact hash 根据规范化文件清单计算，文件清单至少包含相对路径、大小和文件 SHA-256；不得依赖 zip 时间戳、文件写入顺序或宿主机绝对路径。

### 3.3 workspace 原子保存

1. 校验客户端提交的 `workspaceRevision`，不一致时拒绝覆盖。
2. 将完整工作区写入报告目录之外的临时目录。
3. 校验入口、路径、文件数量、总体积、文件类型和 `calcbook.json`。
4. 拒绝绝对路径、`..`、符号链接、设备文件和其他不安全归档内容。
5. 生成或复用 SOURCE artifact。
6. 原子替换 workspace，更新数据库中的 artifact 指针并递增 revision。
7. 不触发预插桩；首次执行通过 artifact build 租约协调懒构建。

源码保存成功不依赖预插桩成功。编辑中的语法或插桩错误不会导致源码丢失，但会阻止运行和发布。

## 4. 数据库分表与字段定义

### 4.1 现有分表问题

数据库表不应仅为了复用旧名称而承担新的混合职责。当前方案需要修正以下问题：

- 不可变 artifact 与可变构建任务混在 `calc_report_artifact`，导致大量条件空字段。
- `workspaceBuildStatus` 落在报告主表，无法同时表达本机与 Docker 的不同 runtime fingerprint。
- bundle manifest 重复写入每次执行历史，artifact GC 也无法通过外键识别 bundle 引用。
- `user_input_history` 同时承担执行审计、进程路由、输入步骤和结果，低频与高频数据相互干扰。
- `calc_report_archive` 与 `input_cache` 都表达最近输入，存在双重数据源。
- dependency selectors 和指定分享用户使用 JSON，数据库无法校验版本归属和用户外键。
- `published_version`、`user_input_history` 和 `input_cache` 当前没有业务调用，因此可以重新评估：版本表改用明确名称，后两者只在职责与名称一致时保留。

因此采用语义优先的分表方式：保留 `calc_report`、分类、实例、收藏和输入缓存等职责明确的表；版本、构建、bundle 和执行使用明确领域名称。

### 4.2 通用字段约定

数据库模型使用一个共享 `Base(DeclarativeBase)`。需要独立身份的业务实体继承抽象 `BaseModel` 并统一包含：

```text
id                  INTEGER PRIMARY KEY AUTOINCREMENT
oid                 CHAR(24) NOT NULL UNIQUE
createdAt           DATETIME(timezone=True) NOT NULL
```

- 主键已经包含索引，不再为 `id` 创建重复普通索引。
- `oid` 必须唯一，只用于 API 和外部标识；表间关联统一使用整数 ID。
- 可变实体增加 `updatedAt`；支持软删除的报告、分类和实例增加 `deletedAt`。
- hash 保存不带 `sha256:` 前缀的 `CHAR(64)`；运行镜像 digest 使用 `VARCHAR(71)`。
- 枚举使用 `SMALLINT + IntEnum + CHECK`，兼容 SQLite 和 PostgreSQL。
- JSON 字段使用 callable default，禁止 `{}`、`[]` 等共享可变默认值。
- 纯关联表直接继承 `Base`，不创建 OID，使用组合主键或组合唯一约束；所有表仍共享同一份 metadata。

跨表枚举集中定义为：

```text
ArtifactKind            SOURCE=1, INSTRUMENTED=2
ArtifactBuildStatus     PENDING=0, BUILDING=1, READY=2, FAILED=3
VersionReviewStatus     PENDING=0, APPROVED=1, REJECTED=2
ExecutionSourceType     WORKSPACE=1, LATEST=2, VERSION=3
ExecutorType            LOCAL=1, DOCKER=2
ExecutionStatus         PENDING=0, RUNNING=1, SUCCEEDED=2,
                        FAILED=3, CANCELLED=4, EXPIRED=5
ShareAccessType         LINK=1, PUBLIC=2, SPECIFIED_USERS=3
ReportOriginType        CREATED=1, COPY=2, SHARE=3, UZC_IMPORT=4
```

### 4.3 报告与分类

#### `calc_report_category`

```text
userId              INTEGER FK users.id NOT NULL
name                VARCHAR(50) NOT NULL
description         TEXT NULL
sortOrder           INTEGER NOT NULL DEFAULT 0
updatedAt           DATETIME NOT NULL
deletedAt           DATETIME NULL
```

删除 `status` 和易漂移的 `total`。建立活跃分类 `(userId, name)` 部分唯一索引，以及 `(userId, deletedAt, sortOrder)` 列表索引。

#### `calc_report`

```text
userId                  INTEGER FK users.id NOT NULL
categoryId              INTEGER FK calc_report_category.id NOT NULL
name                    VARCHAR(100) NOT NULL
description             TEXT NULL
cover                   VARCHAR(500) NULL
entryPath               VARCHAR(255) NOT NULL DEFAULT 'src/main.py'
formatVersion           SMALLINT NOT NULL DEFAULT 1
workspaceRevision       BIGINT NOT NULL DEFAULT 0
workspaceArtifactId     INTEGER FK calc_report_artifact.id NULL
latestVersionId         INTEGER NULL
updatedAt               DATETIME NOT NULL
deletedAt               DATETIME NULL
```

删除 `type`、整数 `version`、`copyFromId`、`isApproved`、`shareType`、`shareToUserIds` 和 build 状态字段。建立活跃报告 `(userId, categoryId, name)` 部分唯一索引，以及 `(userId, deletedAt, updatedAt)` 列表索引。

`workspaceArtifactId` 必须指向 SOURCE artifact。`latestVersionId` 不使用单列外键，而是与 `calc_report.id` 组成命名复合外键，引用 `(calc_report_version.reportId, calc_report_version.id)`，确保 latest 属于当前报告。

#### `calc_report_origin`

来源信息属于可选的一对一关系，不放入报告热表：

```text
reportId                INTEGER FK calc_report.id NOT NULL UNIQUE
originType              SMALLINT NOT NULL
sourceReportId          INTEGER FK calc_report.id NULL
sourceVersionId         INTEGER FK calc_report_version.id NULL
sourceArtifactId        INTEGER FK calc_report_artifact.id NULL
sourceArchiveHash       CHAR(64) NULL
metadata                JSON NULL
```

`originType` 为 CREATED、COPY、SHARE 或 UZC_IMPORT。来源 artifact 形成持久引用，保证后续 workspace 修改后仍能审计初始来源。

### 4.4 Artifact 与预插桩构建

#### `calc_report_artifact`

只保存已完成原子发布的不可变对象：

```text
artifactKind            SMALLINT NOT NULL          # SOURCE/INSTRUMENTED
contentHash             CHAR(64) NOT NULL UNIQUE
storageKey              VARCHAR(500) NOT NULL UNIQUE
manifest                JSON NOT NULL
fileCount               INTEGER NOT NULL CHECK >= 0
totalSize               BIGINT NOT NULL CHECK >= 0
formatVersion           SMALLINT NOT NULL CHECK >= 1
```

该表不保存 build status、错误、lease、runtime fingerprint 或访问热度。artifact GC 根据外键引用和活动租约判断，不在每次读取时更新数据库。

#### `calc_report_artifact_build`

可变构建任务单独保存：

```text
sourceArtifactId        INTEGER FK calc_report_artifact.id NOT NULL
runtimeFingerprint      VARCHAR(255) NOT NULL
outputArtifactId        INTEGER FK calc_report_artifact.id NULL
status                  SMALLINT NOT NULL             # PENDING/BUILDING/READY/FAILED
diagnostics             JSON NULL
attemptCount            INTEGER NOT NULL DEFAULT 0
leaseOwner              VARCHAR(128) NULL
leaseExpiresAt          DATETIME NULL
startedAt               DATETIME NULL
completedAt             DATETIME NULL
updatedAt               DATETIME NOT NULL
```

约束 `(sourceArtifactId, runtimeFingerprint)` 唯一。READY 必须存在 output artifact；非 BUILDING 状态不得保留有效 lease。索引 `(status, leaseExpiresAt)` 供 worker 抢占和超时恢复。

build 不包含 `reportId`，相同 SOURCE 和 runtime 可以跨报告复用。报告当前构建状态通过 `workspaceArtifactId + runtimeFingerprint` 查询，不落到 `calc_report`。

### 4.5 发布版本与审核

#### `calc_report_version`

使用清晰表名替代旧 `published_version`：

```text
reportId                INTEGER FK calc_report.id NOT NULL
sourceArtifactId        INTEGER FK calc_report_artifact.id NOT NULL
major                   INTEGER NOT NULL CHECK >= 0
minor                   INTEGER NOT NULL CHECK >= 0
patch                   INTEGER NOT NULL CHECK >= 0
description             TEXT NULL
publishedByUserId       INTEGER FK users.id NOT NULL
reviewStatus            SMALLINT NOT NULL DEFAULT PENDING
reviewedByUserId        INTEGER FK users.id NULL
reviewedAt              DATETIME NULL
reviewComment           TEXT NULL
```

版本字符串 `1.2.3` 和 import segment `v_1_2_3` 均从数字字段派生，不重复落库。约束 `(reportId, major, minor, patch)` 唯一，并增加 `(reportId, id)` 唯一键供复合外键引用。

版本、SOURCE artifact 和版本号不可修改。审核状态属于不可变发布版本；只有 APPROVED 版本可以创建分享链接。工具链升级只新增 artifact build，不产生新业务版本。

### 4.6 Workspace 依赖与 selector

#### `calc_report_dependency`

```text
reportId                INTEGER FK calc_report.id NOT NULL
targetReportId          INTEGER FK calc_report.id NOT NULL
alias                   VARCHAR(64) NOT NULL
updatedAt               DATETIME NOT NULL
```

约束 `(reportId, alias)` 唯一、`reportId != targetReportId`，并增加 `(id, targetReportId)` 唯一键供 selector 复合引用。

#### `calc_report_dependency_selector`

```text
dependencyId            INTEGER FK calc_report_dependency.id NOT NULL
targetReportId          INTEGER FK calc_report.id NOT NULL
selectorKey             VARCHAR(32) NOT NULL
targetVersionId         INTEGER FK calc_report_version.id NULL
isDefault               BOOLEAN NOT NULL DEFAULT FALSE
```

- `(dependencyId, selectorKey)` 唯一。
- 每个 dependency 通过部分唯一索引保证最多一个 `isDefault = TRUE`。
- `latest` 要求 `targetVersionId IS NULL`；明确版本要求非空。
- 复合外键保证 selector 的 target report 与 dependency 一致，并保证明确版本属于 target report。
- 至少一个 selector 且恰好一个 default 由 dependency service 在事务内保证。

workspace 保存时把 dependency 和 selector 快照写入 SOURCE manifest。发布版本通过 SOURCE artifact 获得不可变声明，不再单独复制 dependency JSON。

### 4.7 分享

#### `calc_report_share_link`

```text
versionId               INTEGER FK calc_report_version.id NOT NULL
tokenHash               CHAR(64) NOT NULL UNIQUE
accessType              SMALLINT NOT NULL             # LINK/PUBLIC/SPECIFIED_USERS
expiresAt               DATETIME NULL
revokedAt               DATETIME NULL
maxUseCount             INTEGER NULL CHECK >= 0
useCount                INTEGER NOT NULL DEFAULT 0 CHECK >= 0
createdByUserId         INTEGER FK users.id NOT NULL
```

report 和 artifact 均由 version 推导，不重复保存。创建链接时要求 version 已 APPROVED；`useCount` 使用条件更新原子递增。

#### `calc_report_share_recipient`

```text
shareLinkId             INTEGER FK calc_report_share_link.id
userId                  INTEGER FK users.id
PRIMARY KEY (shareLinkId, userId)
```

使用关联表替代 `allowedUserIds` JSON。SPECIFIED_USERS 必须至少存在一个 recipient，由 share service 在同一事务中保证。

### 4.8 Bundle 与 artifact 引用

#### `calc_execution_bundle`

```text
bundleHash                  CHAR(64) NOT NULL UNIQUE
runtimeFingerprint          VARCHAR(255) NOT NULL
runtimeImageDigest          VARCHAR(71) NULL
entrySourceArtifactId       INTEGER FK calc_report_artifact.id NOT NULL
entryExecutionArtifactId    INTEGER FK calc_report_artifact.id NOT NULL
manifest                    JSON NOT NULL
formatVersion               SMALLINT NOT NULL DEFAULT 1
```

bundle 是与用户和执行会话无关的不可变内容对象。manifest 用于传输，关系表用于数据库完整性和 GC。

#### `calc_execution_bundle_component`

```text
bundleId                    INTEGER FK calc_execution_bundle.id NOT NULL
componentKey                VARCHAR(160) NOT NULL
scopeKey                    VARCHAR(80) NOT NULL
alias                       VARCHAR(64) NULL
selectorKey                 VARCHAR(32) NULL
sourceArtifactId            INTEGER FK calc_report_artifact.id NOT NULL
executionArtifactId         INTEGER FK calc_report_artifact.id NOT NULL
isEntry                     BOOLEAN NOT NULL DEFAULT FALSE
```

`componentKey` 对入口固定为 `entry`，对依赖使用规范化的 `scope/alias/selector`。约束 `(bundleId, componentKey)` 唯一，并用部分唯一索引保证每个 bundle 最多一个 entry；至少一个 entry 由 bundle service 在事务内保证。entry 的 alias/selector 为空，依赖 component 必须非空。component 外键使 artifact 引用可查询，无需解析 JSON 才能执行 GC。

### 4.9 执行与交互输入

#### `calc_execution`

保存低频执行状态和可复现审计信息：

```text
userId                  INTEGER FK users.id NOT NULL
reportId                INTEGER FK calc_report.id NOT NULL
bundleId                INTEGER FK calc_execution_bundle.id NOT NULL
sourceType              SMALLINT NOT NULL       # WORKSPACE/LATEST/VERSION
resolvedVersionId       INTEGER FK calc_report_version.id NULL
executorType            SMALLINT NOT NULL       # LOCAL/DOCKER
status                  SMALLINT NOT NULL
sandboxExecutionId      VARCHAR(64) NULL UNIQUE
executorNodeId          VARCHAR(128) NULL
startedAt               DATETIME NULL
lastActiveAt            DATETIME NULL
expiresAt               DATETIME NULL
completedAt             DATETIME NULL
resultPath              VARCHAR(500) NULL
errorCode               VARCHAR(64) NULL
errorMessage            TEXT NULL
metrics                 JSON NULL
```

WORKSPACE 要求 `resolvedVersionId IS NULL`；LATEST/VERSION 要求非空。复合外键保证 resolved version 属于当前 report。索引覆盖 `(userId, createdAt)`、`(reportId, createdAt)` 和 `(status, expiresAt)`。

#### `user_input_history`

保留表名，但只保存高频变化的交互状态，与 execution 一对一：

```text
executionId             INTEGER FK calc_execution.id NOT NULL UNIQUE
defaults                JSON NOT NULL
inputHistory            JSON NOT NULL
currentStep             INTEGER NOT NULL DEFAULT 0
totalSteps              INTEGER NOT NULL DEFAULT 0
updatedAt               DATETIME NOT NULL
```

删除文件路径、发布状态、结果 HTML、executor、bundle 和错误字段。交互更新不改写 `calc_execution` 的 bundle 与来源审计字段。

#### `input_cache`

只保存用户最近一次输入：

```text
userId                  INTEGER FK users.id NOT NULL
reportId                INTEGER FK calc_report.id NOT NULL
entryName               VARCHAR(128) NOT NULL
sourceArtifactId        INTEGER FK calc_report_artifact.id NOT NULL
defaults                JSON NOT NULL
updatedAt               DATETIME NOT NULL
expiresAt               DATETIME NULL
```

约束 `(userId, reportId, entryName)` 唯一。source artifact 只用于判断字段结构是否可能变化，不参与唯一键。删除职责重复的 `calc_report_archive`。

### 4.10 计算实例与收藏

#### `calc_report_instance_category`

与报告分类相同，使用 `sortOrder`、`updatedAt`、`deletedAt`，删除 `status` 和 `total`。

#### `calc_report_instance`

```text
userId                  INTEGER FK users.id NOT NULL
categoryId              INTEGER FK calc_report_instance_category.id NOT NULL
reportId                INTEGER FK calc_report.id NOT NULL
sourceVersionId         INTEGER FK calc_report_version.id NULL
bundleId                INTEGER FK calc_execution_bundle.id NOT NULL
executionId             INTEGER FK calc_execution.id NULL
reportName              VARCHAR(100) NULL
name                    VARCHAR(100) NOT NULL
description             TEXT NULL
defaults                JSON NOT NULL
resultPath              VARCHAR(500) NOT NULL
revision                BIGINT NOT NULL DEFAULT 1
updatedAt               DATETIME NOT NULL
deletedAt               DATETIME NULL
```

workspace 实例通过 bundle 固定源码；发布版本实例同时保存 sourceVersionId。即使执行历史后续清理，bundle 与版本仍能复现实例来源。

#### `favorite_calc_reports`

使用 `(userId, reportId)` 组合主键并保留 `createdAt`，不再创建无业务用途的 OID。

### 4.11 模型与迁移边界

- 所有 ORM 模型统一使用同一个 `Base.metadata`；实体继承 `BaseModel`，关联表直接继承 `Base`，删除 `user_input_history.py` 中的第二套 declarative base。
- Alembic `target_metadata` 只使用 `Base.metadata`。
- 不再创建 `calc_report_archive` 和 `published_version`。
- 重写 `001_initial_schema.py`，合并实例表并删除 `002_calc_report_instance.py`。
- `upgrade` 按 artifact、报告、版本、依赖、分享、bundle、执行、实例顺序创建，`downgrade` 反向删除。
- 全部外键、CHECK、唯一约束和部分索引显式命名。
- 报告、分类和实例使用软删除；workspace dependency、input cache、收藏和 share recipient 在所有者硬删除时 CASCADE。
- 已被版本、分享、bundle 或实例引用的 artifact/version/bundle 使用 RESTRICT；实例的可选 execution 被清理时使用 SET NULL。
- `calc_report` 与 version 的循环引用、selector 的目标归属、execution 的 resolved version 和 instance 的 source version 均使用命名复合外键。
- latest 循环外键在 report/version 两表创建完成后添加：PostgreSQL 使用 `ALTER TABLE`，SQLite 使用 Alembic batch recreate；downgrade 先移除该约束。
- 不读取、转换或迁移现有数据库数据。

## 5. 多版本引用与依赖固化

### 5.1 用户 import 形式

```python
# 使用依赖声明中的 default selector
from calcdeps.continuous_beam.api import calculate_capacity

# 新执行时解析目标报告的 latest
from calcdeps.continuous_beam.latest.api import calculate_capacity

# 永久绑定明确版本
from calcdeps.continuous_beam.v_1_2_1.api import calculate_capacity
```

源码中不出现目标 OID、artifact hash 或物理路径。

### 5.2 解析规则

- `latest` 读取目标报告的 `latestVersionId`，为空时拒绝引用。
- `v_1_2_1` 读取目标报告不可变的明确版本。
- 省略 selector 时使用依赖声明的 default，默认是 latest。
- 每次新建 bundle 时在同一数据库读事务中解析整个依赖闭包。
- 解析结果写入 bundle manifest；活动会话永不重新解析 latest。
- 同一 artifact 可被多个 alias 或 selector 使用，但只存储和传输一次。
- 循环检测以已解析的报告、版本和 artifact 节点为准。

### 5.3 报告局部命名空间

平铺的全局 `calcdeps` 无法正确支持传递依赖中的同名 alias。预插桩构建器因此将托管源码中的静态 `calcdeps` import 改写为 artifact 作用域内部命名空间：

```text
用户源码:
  calcdeps.common.latest.api

执行产物:
  __uzon_deps__.scope_{sourceHash}.common.latest.api
```

每个 SOURCE artifact 拥有独立 scope，入口和传递依赖中的 `common` 不会互相覆盖。用户仍只编写公开的 `calcdeps` 形式。

第一阶段仅支持可静态识别的 `import` 和 `from ... import ...`。使用 `importlib`、`__import__` 或字符串拼接动态加载 `calcdeps` 时构建失败；后续如需动态能力，应提供显式受控的依赖加载 API，而不是开放任意模块路径。

## 6. 预插桩执行 artifact

### 6.1 现有运行时插桩的问题

当前 `@uzon_calc` 和 `@uzon_calc_func` 在模块 import 时调用 `instrument_function()`：读取函数源码、转换 AST、编译并 `exec` 新函数。内存缓存以函数对象为 key，只在单进程内有效，无法跨本机子进程或 Docker 容器复用。

托管 CalcReport 应把这一步前移到 workspace 保存之后，运行时只加载已生成文件。

### 6.2 构建键与工具链指纹

```text
toolchainFingerprint =
  uzoncalcVersion
  + instrumentationFormatVersion
  + pythonImplementation
  + pythonMajorMinor
  + runtimeBuildId

derivationKey = SHA256(
  sourceArtifactHash
  + toolchainFingerprint
)
```

Docker 的 `runtimeImageDigest` 是 runtimeBuildId 的权威实现；本机运行使用相同依赖锁和构建标识生成等价 fingerprint。

### 6.3 异步构建状态机

```text
PENDING -> BUILDING -> READY
                   -> FAILED
```

1. workspace 保存 SOURCE artifact 后幂等创建构建任务。
2. worker 获取 derivation lease，避免多实例重复构建。
3. worker 对整个源码树做纯 AST 转换和静态校验。
4. worker 不 import、exec 或运行任何用户模块和顶层代码。
5. worker输出镜像目录结构的 `.py` 文件、source map 和 instrumentation manifest。
6. 生成文件通过 `compile()` 语法校验后写入临时目录，再原子发布为 INSTRUMENTED artifact。
7. 完成时更新对应 `calc_report_artifact_build`；报告当前状态始终按最新 `workspaceArtifactId + runtimeFingerprint` 派生，旧 revision 的结果不会覆盖新 workspace。

构建错误按文件、原始行号、错误类型和消息写入 build diagnostics。源码保存仍然成功，但编辑器运行和发布必须拒绝当前 SOURCE/runtime 对应的 `PENDING`、`BUILDING` 或 `FAILED` 状态。

### 6.4 运行时跳过重复插桩

生成文件保留 `@uzon_calc`、`@uzon_calc_func` 的上下文和调用语义，但为已转换函数添加受控的 pre-instrumented marker，并注入 recorder/IR/step runtime 引用。装饰器看到 marker 后只创建现有包装函数，不再调用 AST 插桩器。

托管执行入口增加强校验：

- manifest 的 SOURCE hash、toolchain fingerprint 和文件 hash 必须匹配。
- 入口和依赖必须全部来自 READY 的 INSTRUMENTED artifact。
- 缺失产物时触发或等待异步构建，并返回稳定的 `EXECUTION_ARTIFACT_NOT_READY`，不得回退到运行时插桩。

普通本地 Python 脚本、CLI 和旧 `.uzc` 不属于托管 CalcReport，继续保留现有运行时插桩兼容路径。

### 6.5 工具链升级

toolchain fingerprint 变化时：

- SOURCE artifact 和业务版本保持不变。
- 原 INSTRUMENTED artifact 不删除，但不能被新运行时使用。
- 部署任务预热 latest、近期 workspace 和高频版本。
- 尚未预热的版本在首次请求时进入 PENDING；执行不会使用旧工具链或临时插桩。

## 7. Execution Bundle

### 7.1 Bundle manifest

```json
{
  "formatVersion": 1,
  "runtimeFingerprint": "uzoncalc-...",
  "runtimeImageDigest": "sha256:...",
  "entry": {
    "reportOid": "67ab...",
    "sourceType": "latest",
    "resolvedVersion": "1.2.1",
    "sourceArtifactHash": "sha256:source...",
    "executionArtifactHash": "sha256:exec...",
    "entryPath": "src/main.py"
  },
  "scopes": {
    "scope_sourceHash": {
      "continuous_beam": {
        "default": "latest",
        "selectors": {
          "latest": "sha256:exec-latest...",
          "v_1_2_1": "sha256:exec-version..."
        }
      }
    }
  }
}
```

`bundleHash` 根据规范化 manifest 计算，不包含用户授权 token、节点 ID、临时路径或时间戳。manifest 保存到 `calc_execution_bundle`，每个源码和执行 artifact 同时写入 `calc_execution_bundle_component`，用于引用审计和 GC。权限校验与内容寻址必须分离，知道 bundle hash 不代表有权执行。

### 7.2 执行来源

```text
WORKSPACE
  使用当前 workspace SOURCE 和对应 READY 执行产物

LATEST
  立即解析 latestVersionId，并把明确版本写入执行历史

VERSION
  使用请求指定的不可变版本
```

编辑器默认运行 WORKSPACE，普通查看器和正式执行默认运行 LATEST。未发布报告可以运行 WORKSPACE，但不能运行 LATEST、被引用或分享。

## 8. 执行后端选择与本机 sandbox

部署通过 `sandbox.mode` 全局选择 `in_process`、Linux `bubblewrap` 或独立远程 `docker` 服务。三种后端使用相同 bundle、会话和运行时 fingerprint 接口，不再向 executor 传递用户目录的 `script_path` 和 `package_root`。`in_process` 仅用于部署者明确接受同进程风险的环境；`bubblewrap` 和 Docker 均为每次执行提供独立进程边界。

### 8.1 执行流程

1. 主 API 完成报告权限、执行来源和依赖解析。
2. 为全部 SOURCE/runtime 组合取得或等待数据库 build 租约；租约持有者在独立 helper 进程执行纯 AST 构建，其余并发请求共享结果。
3. 生成 bundle manifest 和 bundle hash。
4. Bundle assembler 按 hash 组装或复用只读目录。
5. 为本次执行创建独立 `/work` 和 `/output`。
6. 按配置在进程内、bubblewrap 子进程或远程 Docker 容器加载预插桩入口。
7. 创建 `calc_execution`，将进程通信通道和租约写入执行管理器；交互 defaults 和步骤单独写入一对一的 `user_input_history`。
8. 完成、取消、超时或异常时终止整个进程组并释放租约。

`bubblewrap` 后端不得在主 API 进程 import 用户代码，并为每次执行使用新子进程，避免 `sys.modules`、全局变量、线程和 monkey patch 污染后续计算。`in_process` 是显式配置的兼容后端，不提供该隔离保证。

### 8.2 本机缓存层

| 缓存 | Key | 生命周期 |
| --- | --- | --- |
| SOURCE artifact | source hash | 被 workspace、版本或分享引用期间保留 |
| INSTRUMENTED artifact | derivation key/content hash | 跨执行保留，工具链变化后自然不命中 |
| bundle assembly | bundle hash | 跨子进程复用，LRU/TTL 回收 |
| 执行会话 | execution ID | 交互完成、取消或超时后销毁 |
| 输入缓存 | user/report/entry | 数据库 TTL，记录来源 SOURCE 供结构变化判断 |

bundle assembly 使用硬链接、只读 bind 或安全复制组合 artifact，不修改内容寻址目录。GC 不得删除活动 bundle lease 引用的 artifact。

### 8.3 交互继续执行

`continue` 只接收：

```text
executionId
defaults
```

它必须路由到原子进程，只更新 `calc_execution.lastActiveAt` 和 `user_input_history`，不重新解析 latest、不重建 bundle、不传输 artifact，也不重新插桩。API 重启、进程丢失或超时后不能透明恢复 Python 内存状态，应把执行标记为 `FAILED` 或 `EXPIRED`，由用户重新开始执行。

## 9. Docker sandbox 运行与缓存

Docker 阶段复用本机阶段的 bundle manifest、artifact 格式和执行记录，只替换 orchestrator 与传输实现。

### 9.1 内部协议

```text
POST /sandbox/bundles/prepare
PUT  /sandbox/artifacts/{artifactHash}
POST /sandbox/execute
POST /sandbox/continue
POST /sandbox/terminate
```

流程：

1. Orchestrator 选择具有目标 runtime image 的节点。
2. `prepare` 返回该节点缺失的 SOURCE 和 INSTRUMENTED artifact hash。
3. 主 API 只上传缺失内容，或提供对象存储短期签名地址。
4. 节点在临时目录校验 manifest、文件 hash 和安全解压规则。
5. 校验成功后原子发布到节点 artifact cache。
6. 节点按 bundle hash 组装只读 `/bundle`。
7. 容器获得独立 `/work`、`/output`，并为每次执行启动独立子进程。

容器从 INSTRUMENTED artifact 组装可执行代码，从 SOURCE artifact 只读组装 manifest 声明的资源；不得把 SOURCE 中未插桩的 `src` 目录加入 Python 搜索路径。容器不挂载 `data/calc-reports`、整个用户目录、数据库凭据或 Docker socket。

### 9.2 Docker 缓存层

| 缓存 | Key | 生命周期 |
| --- | --- | --- |
| 运行镜像 | image digest | 由容器运行时管理 |
| 节点 artifact cache | source/execution artifact hash | 跨容器，LRU/TTL/容量回收 |
| 节点 bundle assembly | bundle hash | 跨容器或租约复用 |
| 容器租约 | userId + bundleHash + image digest | 短期空闲复用 |
| 子进程会话 | execution ID | 单次交互执行 |

容器不得跨用户、bundle 或 image digest 复用。bundle 相同只表示内容相同，不取消用户授权和会话隔离检查。

### 9.3 缓存竞争与故障

- artifact 上传幂等，未完成上传对执行请求不可见。
- hash 或解压校验失败时删除临时内容，不能发布缓存项。
- `prepare` 后 artifact 被 GC 时，`execute` 返回可重试 cache miss，主 API 重新 prepare。
- GC 使用租约引用计数，不能删除活动容器使用的 artifact。
- 节点丢失或容器异常时终止会话，不尝试迁移进程内状态。
- runtime image digest 变化时容器、bundle 和 INSTRUMENTED artifact 按 fingerprint 重新匹配。

### 9.4 安全基线

- 非 root 用户、只读根文件系统、删除 Linux capabilities。
- `no-new-privileges`，禁止 privileged、宿主 PID/IPC 和 Docker socket。
- CPU、内存、进程数、文件大小、运行时间和临时磁盘限额。
- 默认禁止网络，扩展联网能力必须经显式权限和受控代理。
- 固定镜像和第三方依赖，不允许运行时安装软件包。
- 配置 seccomp/AppArmor；公开多租户部署可进一步采用 gVisor 或 Kata。

## 10. 分享与 `.uzc` 导入

### 10.1 分享导入

分享只能固定到审核状态为 APPROVED 的发布版本，只传递 SOURCE artifact 和已解析来源信息，不传递 INSTRUMENTED artifact。接收者导入后：

1. 创建自己的 report OID 和 workspace。
2. 重建依赖目标映射，但保留用户源码中的 alias。
3. 创建接收者自己的初始发布版本并设为 latest。
4. 根据接收者当前 toolchain 异步生成 INSTRUMENTED artifact。
5. 记录来源报告、版本、SOURCE artifact 和分享记录。

### 10.2 `.uzc` 导入

现有 `.uzc` 通过兼容适配器转换：

1. 安全解析归档，不调用 `extractall()` 直接信任路径。
2. 拒绝路径穿越、符号链接、压缩炸弹、超大文件和异常文件数量。
3. 读取入口清单并恢复源码树。
4. 生成平台 `calcbook.json` 和 SOURCE artifact。
5. 保持未发布和 `not_requested` 构建状态，首次执行时懒构建。
6. 导入阶段不执行任何用户代码。

后续 `.uzc` 可以扩展 SOURCE manifest 和依赖声明，但派生执行文件仍不作为跨运行时交换格式。

## 11. API 与状态契约

### 11.1 workspace

```text
PUT /calc-report/{reportOid}/workspace
  request:  workspaceRevision + complete workspace
  response: reportOid, workspaceRevision, sourceArtifactHash,
            buildStatus, publishState

GET /calc-report/{reportOid}/workspace/build
  response: sourceArtifactHash, toolchainFingerprint,
            buildStatus, diagnostics
```

build 响应来自 `calc_report_artifact_build`，不从报告主表读取状态。

### 11.2 version

```text
POST /calc-report/{reportOid}/versions
  body: { versionName, description? }
  只要求 SOURCE 通过静态语法和依赖声明校验，不触发目标工具链构建

GET /calc-report/{reportOid}/versions
  返回全部发布版本和 latest 标记

PUT /calc-report/{reportOid}/latest
  body: { versionName }
  只移动 latest 指针

POST /calc-report/{reportOid}/workspace/restore
  body: { versionName }
  只替换 workspace，并触发预插桩
```

版本响应由 major/minor/patch 派生 `versionName` 和 import segment；版本审核接口只更新 review 字段，不允许修改源码 artifact 或版本号。

### 11.3 execution

```text
CalcExecutionSource
  { type: "workspace" }
  { type: "latest" }
  { type: "version", versionName: "1.2.1" }
```

执行响应和历史至少记录：

```text
executionId
sourceType / resolvedVersion
sourceArtifactHash / executionArtifactHash
bundleHash / runtimeFingerprint
executorType
isCompleted / resultPath / windows
```

首次执行等待懒构建；等待超时统一返回稳定业务错误 `EXECUTION_ARTIFACT_NOT_READY`，构建失败返回 `EXECUTION_ARTIFACT_BUILD_FAILED` 和结构化诊断。AST 插桩只在独立 helper 进程执行，不在主 API 进程执行用户模块或顶层代码。

## 12. 发布状态

`CalcPublishState` 不单独落库，根据 artifact 指针派生：

```text
latestVersionId 为空
  -> unpublished

workspaceArtifactId == latest.sourceArtifactId
  -> published

workspaceArtifactId 匹配其他发布版本
  -> workspace_version_mismatch

其它情况
  -> unpublished_changes
```

构建状态与发布状态相互独立，并根据当前 runtime 对应的 artifact build 派生。例如 workspace 可以是 `unpublished_changes + BUILDING` 或 `published + FAILED`。列表和编辑器同时显示两个状态；普通查看器只展示本次实际执行的版本和 runtime，不展示 workspace 警告。

## 13. 实施阶段

1. **数据库与 SOURCE 存储**：统一 BaseModel 和初始迁移，实现规范化报告、artifact、版本、依赖、bundle、执行和实例表。
2. **预插桩构建**：实现 artifact build 状态机、纯 AST 文件构建器、诊断、source map 和 INSTRUMENTED artifact。
3. **版本与依赖**：实现发布/latest/恢复、版本审核、关系型 selector、依赖快照和作用域 import 改写。
4. **执行后端**：实现共用 bundle/component 契约和 `in_process`、`bubblewrap`、远程 Docker 三种配置后端，分别落地执行审计与交互输入历史。
5. **分享和导入**：在 SOURCE artifact 与依赖模型上实现固定版本分享和安全 `.uzc` 导入。
6. **Docker sandbox**：实现独立服务的 prepare/upload/execute 协议、节点缓存、容器租约和资源隔离。

三种后端在同一阶段完成，并共用协议、缓存键和失败语义，避免因部署模式修改 bundle 和数据库契约。

## 14. 验收场景

### 14.1 workspace 与版本

1. 新报告保存后只有 workspace，状态为 `unpublished + not_requested`；首次预览等待构建 READY，未发布内容仍不能被引用或分享。
2. 发布 `1.0.0` 后 latest 指向该版本；再次保存 workspace 不改变 latest。
3. 发布 `1.1.0` 后新执行使用 `1.1.0`，旧 bundle 和活动会话仍使用原版本。
4. latest 回退只移动指针；从版本恢复只修改 workspace。
5. `latest.json` 丢失或损坏时可根据数据库重建。

### 14.2 预插桩

1. 保存立即返回 PENDING，后台成功转为 READY。
2. 语法或插桩失败不丢失源码，但运行和发布返回结构化诊断。
3. workspace 连续保存时，旧构建结果不能覆盖新 revision。
4. 相同 SOURCE 和 toolchain 只生成一个派生产物。
5. 工具链升级后 SOURCE 和业务版本不变，只重建执行 artifact。
6. 代表性计算书的公式记录、错误行号和 HTML 结果与现有运行时插桩保持一致。

### 14.3 多版本依赖

1. 同一执行可以同时引用 dependency 的 latest、`v_1_0_0` 和 `v_1_1_0`。
2. latest 在 bundle 创建后变化不影响该 bundle。
3. 入口和传递依赖使用同名 alias 时，通过 artifact scope 得到各自目标。
4. 未声明 selector、workspace selector、越权版本和循环依赖均被拒绝。
5. 动态拼接 `calcdeps` import 在构建阶段被拒绝。

### 14.4 缓存与执行

1. 本机 bundle cache 命中时不重新组装 artifact。
2. Docker artifact cache 命中时上传字节数为零。
3. 单个 dependency 更新时不重传未变化 artifact。
4. `continue` 不重新解析版本、传输 bundle 或执行插桩。
5. GC 不删除活动 lease 引用内容。
6. 进程、容器或节点丢失时执行历史得到明确终态。
7. 用户代码无法访问 bundle manifest 未声明的报告、宿主目录或服务凭据。

### 14.5 数据库约束

1. SQLite 可在启用 foreign key 后完成 upgrade、downgrade 和再次 upgrade；PostgreSQL 离线 DDL 可生成。
2. latest、dependency selector 和 execution resolved version 不能引用其他报告的版本。
3. 每个 dependency 恰好一个 default selector，每个 bundle 恰好一个 entry component。
4. artifact 与 artifact build 分离；READY build 必须存在 output artifact。
5. 分享只能引用 APPROVED 版本，指定用户通过 recipient 外键表保存。
6. 高频交互更新只修改 `user_input_history`，不会重写 bundle 或执行来源审计。
7. schema 不再包含 `calc_report_archive`、`published_version` 和第二套 metadata。

## 15. 关键结论

- `CalcReport` 是唯一顶层领域对象，物理存储使用 report OID。
- workspace 是可编辑 SOURCE，published version 是不可变 SOURCE，latest 是数据库指针。
- 数据表按报告、不可变 artifact、构建任务、版本、依赖 selector、bundle component、执行审计和交互状态拆分。
- 依赖声明随 SOURCE 固化，latest 在每次 bundle 构建时解析，历史执行永久固定结果。
- 预插桩以 SOURCE 和 toolchain 为输入生成文件 artifact，托管运行时禁止临时插桩。
- 本机和 Docker 共用 bundle、artifact、fingerprint、执行审计和交互状态契约。
- 内容缓存与授权分离；缓存命中不能绕过报告、版本或分享权限。
