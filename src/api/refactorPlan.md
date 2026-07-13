# 计算书存储、分享、导入与执行架构重构思路

## 1. 背景

当前计算书由数据库记录和单个 Python 文件共同组成，源码路径按以下规则生成：

```text
data/calcs/{userId}/{categoryName}/{reportName}.py
```

这种方式实现简单，也便于早期直接编辑和执行单文件计算书。但随着多文件计算项目、计算书分享、`.uzc` 导入、跨计算书引用和服务器多用户部署等需求出现，名称、目录、身份和 Python 导入之间开始互相制约。

本次重构的核心方向是：

> 将计算书从“数据库记录对应一个按名称保存的 Python 文件”，提升为“具有稳定身份、文件树、版本、依赖和执行清单的计算项目包”。

## 2. 目标

重构后的架构应支持：

1. 用户通过分享链接导入其他用户的计算书，并安全处理名称冲突。
2. 一个计算书包含入口脚本、辅助 Python 文件和资源文件。
3. 用户可以引用自己的其他计算书，但不需要知道内部唯一 ID 或物理路径。
4. 导入 `uzoncalc zip` 生成的 `.uzc`，保留其本地依赖和目录结构。
5. 分享、导入和执行的计算书一律按不可信代码处理。
6. 服务器通过短生命周期容器运行代码，同时支持交互式计算在短期内保持执行状态。
7. 展示名称、分类、物理存储、Python import 和版本可以分别演进。

## 3. 现有方案的主要问题

### 3.1 名称承担了过多职责

当前名称同时参与：

- UI 展示。
- 数据库判重。
- 物理文件路径生成。
- Python 文件名和潜在模块名生成。
- 分类目录组织。

因此计算书改名或移动分类时必须同步移动源码文件。分类本应只是 UI 组织信息，却直接影响运行路径。加入版本、分享来源和依赖后，这种耦合会使任何名称调整都可能破坏执行环境。

### 3.2 跨分类同名规则不一致

保存前的名称检查按同一分类判重，但实际保存时会先按 `userId + name` 全局查找计算书。跨分类创建同名计算书时，可能把另一分类中的记录识别为待更新对象。

这说明名称不能继续作为计算书身份或主要查找键。服务层必须以稳定项目 ID 定位更新对象，名称只能作为展示属性或有限范围内的业务约束。

### 3.3 单文件模型不能表达计算项目

现有保存接口只接收一段 `code` 并写入一个 `.py` 文件，无法自然表达：

- 主入口和多个辅助 Python 文件。
- 图片、Excel、JSON 等资源。
- 入口文件路径。
- 项目格式版本。
- 依赖清单和依赖版本。
- 文件完整性哈希。
- 可供其他计算书调用的公共模块。

### 3.4 Python import 缺少可靠隔离

当前运行逻辑临时将用户目录和脚本目录加入进程级 `sys.path`。常见的 `helper.py`、`common.py` 容易在计算书之间发生模块名冲突。

入口模块缓存只检查入口文件本身，辅助模块变化不一定能使缓存失效。普通导入模块还可能保留在 `sys.modules` 中，影响后续执行。在服务器多用户环境中，不能继续把进程级 Python 导入状态作为租户隔离手段。

### 3.5 数据库和文件系统无法形成事务

现有流程中可能出现：

- 数据库提交成功，但源码写入失败。
- 文件移动成功，但数据库更新失败。
- 数据库回滚后，已复制的文件仍然存在。
- 逻辑删除后物理文件继续保留，并可能被后续同名计算书覆盖。

需要通过不可变版本、临时写入、原子发布和状态机减少数据库与文件系统的不一致窗口。

### 3.6 分享能力缺少完整边界

现有模型包含审核和分享范围字段，但缺少：

- 不可猜测的分享令牌。
- 分享版本和来源版本。
- 过期、撤销和访问次数策略。
- 导入来源记录。
- 导入后的依赖重映射。
- 统一的所有权和分享授权校验。

正式支持分享前，所有详情读取、源码读取、执行、复制和导入接口都必须统一经过访问控制服务。

### 3.7 `.uzc` 还不是完整交换格式

当前 `.uzc` 能够打包入口目录下静态导入的本地 Python 模块，这是可复用的基础，但其清单信息较少，尚未描述：

- 格式版本。
- 项目元数据和入口类型。
- 文件哈希。
- 资源文件。
- 计算书依赖图。
- 外部 Python 依赖策略。
- 生成工具和 UzonCalc 版本。

服务器不能直接信任归档中的路径或调用 `extractall()`。导入过程必须防止路径穿越、符号链接、压缩炸弹、异常文件数量和超大解压体积，并且不得在导入阶段执行任何代码。

## 4. 核心设计原则

### 4.1 身份、名称和路径解耦

一个计算项目至少需要区分以下概念：

| 概念 | 示例 | 职责 |
| --- | --- | --- |
| 项目 OID | `67ab...` | 数据库关联、权限和物理存储 |
| 展示名称 | `连续梁承载力计算` | UI 展示，可修改 |
| 依赖别名 | `continuous_beam` | 当前项目源码中的 import 名称 |
| 入口路径 | `main.py` | 项目内部入口，由清单管理 |
| 版本 OID | `91cd...` | 指向一次不可变源码快照 |

物理路径不对用户公开，也不写入用户源码。展示名称变化不应移动物理文件，分类变化不应改变执行路径。

### 4.2 计算书是项目包，不是单文件

每个项目拥有独立文件树和项目清单。当前可编辑内容统一放在 `workspace` 下：

```text
workspace/
  calcbook.json
  src/
    main.py
    api.py
    helpers.py
  resources/
```

建议约定：

- `src/main.py` 负责计算书入口、UI 和文档生成。
- `src/api.py` 或清单声明的导出模块负责跨计算书复用。
- 其他源码文件属于项目内部实现。
- 资源文件必须使用项目内相对路径访问。

其他计算书不应直接导入目标项目的 `main.py`，避免执行装饰器、顶层初始化和文档生成等副作用。

### 4.3 `workspace` 可修改，命名版本不可修改

`workspace` 表示当前可编辑内容。用户保存计算书时，服务端原子替换 `workspace`，并记录这次完整内容对应的 artifact hash。保存不会自动改变任何已发布版本，也不会改变其他计算书通过 `latest` 得到的依赖内容。

用户主动发布版本时填写 `MAJOR.MINOR.PATCH` 格式的版本号，例如 `1.2.1`。系统将其转换为可用于 Python import 的目录名 `v_1_2_1`，并在 `version/v_1_2_1` 下保存不可变内容。

第一阶段只支持三个非负整数构成的版本号，不支持 prerelease 和 build metadata。版本名在项目内唯一，已发布版本不得覆盖或修改；修正内容必须发布新版本。

### 4.4 `latest` 是已发布版本指针

`latest` 不再保存可编辑源码，而是指向当前被提升为默认版本的 `CalcProjectVersion`。数据库字段 `latestVersionId` 是唯一权威来源，项目目录下的 `latest.json` 只是便于检查和部署同步的可重建投影。

- 成功发布新版本后，默认将 `latestVersionId` 更新为该版本。
- 系统允许将 `latest` 重新指向任意已有版本，用于回退或重新提升。
- 调整 `latest` 只移动指针，不覆盖或修改 `workspace`。
- 如需在旧版本基础上继续编辑，必须显式执行“从版本恢复到 workspace”。
- 尚无已发布版本时 `latestVersionId` 为空，项目不能被其他计算书引用、正式执行或分享。
- `v_1_2_1` 永久绑定发布时的 content hash。
- 相同内容即使被多个项目或版本使用，也可以复用同一 artifact。
- 正式执行、分享和导入必须记录 `latest` 当时解析到的版本 ID 和 content hash，不能只记录 `latest` 字符串。

因此，引用 `latest` 仍然可以审计和复现：历史执行记录使用当时解析出的已发布 artifact，而不是重新解析后来发生变化的指针。

## 5. 建议领域模型

以下模型用于表达职责，不代表最终数据库字段必须完全按此命名。

```text
CalcProject
  oid
  ownerUserId
  displayName
  categoryId
  entryPath
  workspaceArtifactHash
  latestVersionId
  status

CalcProjectVersion
  oid
  projectId
  versionName
  importSegment
  storageKey
  contentHash
  formatVersion
  createdAt

CalcProjectDependency
  projectId
  alias
  targetProjectId
  defaultSelector
  selectors

CalcArtifact
  contentHash
  storageKey
  fileCount
  totalSize
  formatVersion
  createdAt

CalcShareLink
  tokenHash
  sourceProjectId
  sourceVersionId
  sourceArtifactHash
  expiresAt
  revokedAt
  createdBy

CalcProjectOrigin
  projectId
  sourceType
  sourceProjectId
  sourceVersionId
  sourceArtifactHash
  sourceArchiveHash
```

`defaultSelector` 和 `selectors` 保存逻辑选择器，例如 `latest`、`1.2.1`。版本 OID 和 content hash 仍由后端使用，不暴露到用户源码中。分类只作为项目列表的组织元数据，不参与源码路径构造。

计算书详情和列表响应还应返回以下派生状态：

```text
CalcPublishState
  unpublished
  published
  unpublished_changes
  workspace_version_mismatch

CalcProjectPublishInfo
  workspaceArtifactHash
  workspaceVersionName
  latestVersionId
  latestVersionName
  latestArtifactHash
  publishState
```

状态计算规则如下：

- `unpublished`：项目没有 `latestVersionId`。
- `published`：workspace content hash 与 latest 版本一致。
- `unpublished_changes`：workspace content hash 不匹配任何已发布版本。
- `workspace_version_mismatch`：workspace 匹配某个已发布版本，但该版本不是 latest，常见于 latest 回退或从旧版本恢复 workspace。

## 6. 物理存储建议

服务器永久存储可以使用本地磁盘或对象存储。项目目录按稳定 OID 定位，目录内明确区分当前内容和命名版本：

```text
data/calc-projects/{userId}/{projectOid}/
  workspace/
    calcbook.json
    src/
      main.py
      api.py
    resources/
  latest.json
  version/
    v_1_2_1/
      calcbook.json
      src/
        main.py
        api.py
      resources/
```

`latest.json` 至少记录 `versionOid`、`versionName`、`importSegment`、`contentHash` 和 `updatedAt`。版本目录名用于人工检查和 import 选择，数据库仍以 `latestVersionId` 和版本 OID 关联业务数据。需要扩展到多实例部署时，`storageKey` 可以指向对象存储，而业务层不依赖具体磁盘路径。

不可变 artifact 使用独立的内容寻址存储，避免执行容器直接访问项目目录：

```text
data/calc-artifacts/sha256/{hashPrefix}/{contentHash}/
  manifest.json
  payload.zip
```

`manifest.json` 至少记录规范化相对路径、文件大小和文件 SHA-256。artifact hash 根据规范化文件清单计算，不依赖压缩文件的时间戳或写入顺序。

保存 `workspace` 时采用以下过程：

1. 将新内容写入项目外的临时目录。
2. 校验清单、入口、路径、文件数量、总体积和允许的文件类型。
3. 拒绝绝对路径、`..`、符号链接和其他不能安全归档的文件。
4. 生成规范化文件清单和 content hash，并创建或复用不可变 artifact。
5. 原子替换 `workspace` 目录，更新 `workspaceArtifactHash`。
6. 任一步失败时删除临时内容，不改变当前有效的 workspace 和数据库指针。

发布命名版本时，将当前 `workspaceArtifactHash` 绑定到新的 `CalcProjectVersion`，并原子发布对应的 `version/v_x_y_z`。创建版本记录和更新 `latestVersionId` 必须在同一数据库事务内完成；如果版本名已存在，则直接拒绝。

数据库事务提交后，以临时文件加原子替换方式刷新 `latest.json`。如果刷新失败，不回滚已经成功的版本发布，而是记录告警并由修复任务根据 `latestVersionId` 重建，因为数据库是唯一权威来源。

调整 latest 时只更新 `latestVersionId` 并刷新 `latest.json`，不修改 workspace。将版本恢复到 workspace 是独立操作：读取指定版本 artifact，写入临时目录，校验后原子替换 workspace，并更新 `workspaceArtifactHash`。

## 7. 跨计算书引用

### 7.1 用户不获取真实文件名

用户按展示名称选择依赖，系统为当前项目创建依赖别名，并显式声明本次允许使用的版本集合。例如项目 B 引用“连续梁承载力计算”：

```json
{
  "dependencies": {
    "continuous_beam": {
      "projectOid": "67ab...",
      "default": "latest",
      "selectors": ["latest", "1.2.1"]
    }
  }
}
```

`default` 必须出现在 `selectors` 中。执行包只携带这里声明的版本，不会复制目标项目全部历史版本。

依赖只能声明 `latest` 或已经发布的明确版本。`workspace` 不是合法 selector，也不存在 `calcdeps.<alias>.workspace` import。尚未发布的项目不能作为依赖目标。

### 7.2 三种版本引用形式

项目 B 可以使用以下 import：

```python
# 使用依赖清单中的默认版本，默认值为 latest
from calcdeps.continuous_beam.api import calculate_capacity

# 显式使用 latest
from calcdeps.continuous_beam.latest.api import calculate_capacity

# 显式使用不可变版本 1.2.1
from calcdeps.continuous_beam.v_1_2_1.api import calculate_capacity
```

Bundle Builder 在 `calcdeps/<alias>/` 下生成别名包，将其 `__path__` 扩展到默认选择器对应的已发布版本目录，因此省略版本的 import 不需要复制整套源码。显式版本目录则按声明的 selector 生成。

`latest` 和符合 `v_<major>_<minor>_<patch>` 的名称是跨项目导出根目录下的保留名称。依赖别名必须是合法且非保留的 Python 标识符。

用户不需要知道以下真实路径：

```text
/data/calc-projects/1001/67ab.../version/v_1_2_1/src/api.py
```

### 7.3 依赖别名属于引用方项目

依赖别名不是用户全局名称，而是当前项目中的局部绑定。因此同一用户可以在不同项目中使用相同的 `common`，也可以在一个项目中同时引用两个同名来源：

```python
from calcdeps.common_old.api import calculate as calculate_old
from calcdeps.common_new.api import calculate as calculate_new
```

展示名称修改、物理路径变化或分享导入后重新生成 OID，都不会要求修改源码，只需保持当前项目中的别名映射。

同一别名可以在一次执行中同时引用 `latest` 和一个或多个命名版本，适用于新旧算法对比。所有使用的 selector 必须预先出现在依赖清单中；不能把静态源码扫描作为完整性和权限判断的唯一依据，因为动态 import 和条件 import 可能无法可靠识别。

### 7.4 选择器解析与执行固化

构建执行包时，后端将每个逻辑选择器解析为确定 artifact：

- `latest` 先解析目标项目的 `latestVersionId`，再读取该版本永久绑定的 content hash；`latestVersionId` 为空时拒绝引用。
- `1.2.1` 解析为 `CalcProjectVersion` 永久绑定的 content hash。
- 省略版本的 import 解析为依赖清单中的 `default`，默认是 `latest`。

解析结果写入 bundle manifest。即使执行期间目标项目再次保存，已经创建的 bundle 也不会静默切换内容。

添加或升级依赖时，后端应校验：

- 当前用户是否有权访问目标项目或目标分享版本。
- 别名是否符合 Python 模块命名规则。
- selector 是否存在、是否已声明，以及版本名是否符合约束。
- 是否形成循环依赖。
- 依赖深度、项目数量和总体积是否超过限制。

### 7.5 版本管理接口

目标 API 至少包含：

```text
POST /calc-report/{reportOid}/versions
  body: { versionName }
  发布当前 workspace，并自动将新版本提升为 latest

GET /calc-report/{reportOid}/versions
  返回全部已发布版本和当前 latest 标记

PUT /calc-report/{reportOid}/latest
  body: { versionName }
  将 latest 指向已有版本，不修改 workspace

POST /calc-report/{reportOid}/workspace/restore
  body: { versionName }
  将指定版本内容恢复到 workspace，不修改 latest
```

现有保存接口只保存 workspace，响应从单独的报告 OID 调整为结构化结果：

```text
SaveCalcReportResult
  reportOid
  workspaceArtifactHash
  publishState
```

## 8. 分享与导入

### 8.1 分享采用已解析 artifact

分享链接只能由已发布版本创建。选择 `latest` 分享时，创建过程必须立即解析并固定 `sourceVersionId` 和 `sourceArtifactHash`；分享链接后续不会跟随 `latest` 变化。尚未发布的 workspace 不能分享。分享令牌只用于授权导入，不直接暴露项目 OID，也不作为源码访问路径。

### 8.2 导入生成接收者自己的项目

接收者导入后：

1. 创建新的项目 OID，将源 artifact 写入接收者的初始 workspace。
2. 使用来源版本名创建接收者自己的不可变版本并设为 latest。
3. 复制分享时已解析的依赖 artifact 闭包。
4. 将依赖关系映射到新创建的项目 ID。
5. 保留项目内部依赖别名，使源码无需改写。
6. 记录来源项目、来源版本、artifact hash 和归档哈希。

展示名称冲突可以自动生成 `名称（2）` 或让用户在导入确认时修改。由于物理路径按 OID 存储，展示名称冲突不会造成文件覆盖。

### 8.3 `.uzc` 作为导入来源

现有 `.uzc` 可以通过兼容适配器导入：

1. 在独立导入流程中安全解析归档。
2. 读取现有入口清单。
3. 将归档内 `src` 文件树转换为项目 workspace。
4. 生成平台使用的 `calcbook.json` 和 workspace artifact，保持未发布状态。
5. 不执行任何归档代码。

后续可以扩展 `.uzc` 清单，使其成为正式交换格式，同时保留旧归档兼容读取能力。

## 9. 服务器执行安全框架

所有用户编写、分享或导入的 Python 代码必须按恶意代码处理。主 API 进程不得直接 import 用户代码。

### 9.1 运行镜像与用户 artifact 分离

UzonCalc 核心包、允许使用的第三方 Python 依赖和模板 JS 固化在带 digest 的容器镜像中，由容器运行时缓存镜像层。它们不应在每次执行时放入用户 bundle。

用户 artifact 只包含当前项目源码、资源和声明的项目依赖。执行容器不能读取用户的其他项目，更不能挂载整个 `data/calc-projects/{userId}`。

### 9.2 Bundle 是 artifact 组合清单

执行请求必须显式区分源码来源：

```text
CalcExecutionSource
  { type: "workspace" }
  { type: "latest" }
  { type: "version", versionName: "1.2.1" }
```

编辑器保存后使用 `workspace` 执行当前可编辑内容。普通查看器和未指定来源的正式执行默认使用 `latest`，也可以指定明确版本。`latestVersionId` 为空时，正式执行返回“计算书尚未发布”，但不影响编辑器执行 workspace。

Execution Bundle Builder 根据入口项目和依赖清单生成规范化 bundle manifest：

```json
{
  "formatVersion": 1,
  "runtimeImageDigest": "sha256:...",
  "entry": {
    "sourceType": "latest",
    "versionName": "1.2.1",
    "artifactHash": "sha256:current...",
    "entryPath": "src/main.py"
  },
  "aliases": {
    "continuous_beam": {
      "default": "latest",
      "selectors": {
        "latest": "sha256:latest...",
        "v_1_2_1": "sha256:version..."
      }
    }
  }
}
```

`bundleHash` 根据规范化 manifest 计算，用于标识一次确定的源码和依赖组合。artifact 与 bundle 都是不可变对象，内容变化时生成新 hash，不做原地缓存失效。

容器内可将这些 artifact 组装为：

```text
/bundle/
  current/
    src/
    resources/
  calcdeps/
    continuous_beam/
      __init__.py
      latest/
      v_1_2_1/
```

### 9.3 Artifact 缓存和传输协议

远程 sandbox API 不再接收宿主机 `script_path` 和 `package_root`，而采用以下流程：

1. 主 API 完成权限校验、selector 解析和 bundle manifest 构建。
2. 主 API 调用 `prepare bundle`，sandbox 返回本节点缺失的 artifact hash。
3. 主 API 只上传缺失 artifact，或提供对象存储短期签名地址。
4. sandbox 将上传内容解压到临时目录，校验文件清单和 hash 后原子发布到节点缓存。
5. 主 API 使用 `bundleHash` 和短期执行授权 token 启动执行。
6. sandbox 将缓存 artifact 只读组装到 `/bundle`，为本次执行创建独立 `/work` 和 `/output`。

目标内部接口可以表达为：

```text
POST /sandbox/bundles/prepare
PUT  /sandbox/artifacts/{artifactHash}
POST /sandbox/execute
POST /sandbox/continue
POST /sandbox/terminate
```

`bundleHash` 只负责内容寻址，不是授权凭据。短期 token 至少绑定用户 ID、bundle hash、镜像 digest、过期时间和允许的操作。

单机部署可以让主 API 与 sandbox 使用同一专用 artifact store，避免网络传输，但容器仍然只挂载 artifact 缓存，不挂载项目数据目录。多实例部署使用相同的缺失查询协议，从对象存储或主 API 获取未命中内容。

### 9.4 对执行速度的影响

不挂载整个用户目录会增加首次缓存未命中的准备成本，但不会要求每次执行重新传递全部 bundle：

- 冷缓存首次执行需要计算或读取 artifact、传输缺失字节、校验并解压。
- artifact 缓存命中时只交换 bundle manifest 和控制请求，不上传 artifact 内容。
- 保存 workspace 只产生新的编辑预览 artifact，不改变正式执行或依赖方已经解析的 latest bundle。
- 发布版本通常直接复用 `workspaceArtifactHash`，不需要重新打包相同内容。
- 发布新版本或调整 latest 指针后，新建 bundle 使用新的版本解析结果；已经生成的 bundle 保持原 artifact。
- 交互式 `continue` 只传递 `executionId` 和用户输入，不再次准备 bundle。
- 容器销毁只清理容器和可写工作目录，宿主 sandbox 节点的 artifact 缓存可以继续供新容器使用。

因此，需要区分三类缓存：

| 缓存层 | 缓存内容 | 生命周期 |
| --- | --- | --- |
| 容器镜像缓存 | UzonCalc、Python 依赖、模板 JS | 随镜像 digest 更新 |
| Sandbox artifact 缓存 | 用户项目和依赖的不可变 artifact | 跨容器，按容量和 TTL 回收 |
| 执行租约 | 已组装 bundle、子进程和交互状态 | 短期，执行完成或超时即销毁 |

实现阶段应分别记录 artifact 构建、传输、校验解压、容器启动和 Python 执行耗时。没有真实项目体积分布和部署网络基线前，不预设固定毫秒目标，但必须满足以下行为：

- 缓存命中时 artifact 上传字节数为 0。
- `continue` 不传输 bundle 或 artifact。
- 仅一个项目 artifact 变化时，不重传未变化的依赖 artifact。
- 容器无法通过缓存路径读取 bundle manifest 未声明的项目内容。

### 9.5 短期容器租约

为兼顾交互计算和启动性能，容器可以短期复用，但租约至少绑定到：

```text
userId + bundleHash + runtimeImageDigest
```

容器不得跨用户或跨 bundle 复用。以下情况应销毁并重建容器：

- bundle hash 或运行镜像 digest 变化。
- 空闲 TTL 到期。
- 达到最大运行次数或最长生存时间。
- 执行超时、OOM、异常退出或资源违规。
- 用户主动重置执行环境。

容器复用只是性能优化，不能作为安全边界。

### 9.6 每次执行使用独立子进程

容器内的控制服务不得将用户代码 import 到自身进程。每次计算启动独立 Python 子进程：

- UI 交互期间保留该子进程。
- 继续执行请求路由到对应子进程。
- 完成、取消或超时后终止整个进程组。
- 下一次执行使用新的子进程和干净临时目录。

这样可以避免 `sys.modules`、全局变量、线程和 monkey patch 污染后续执行。

### 9.7 容器安全基线

执行容器至少需要：

- 使用非 root 用户。
- 根文件系统只读。
- 删除全部 Linux capabilities。
- 启用 `no-new-privileges`。
- 禁止 privileged、宿主 PID/IPC 和 Docker socket。
- 限制 CPU、内存、进程数、文件大小和临时磁盘。
- 默认禁用网络。
- 固定运行镜像和依赖版本，不允许运行时安装包。
- 配置 seccomp 和 AppArmor；公开多租户部署可进一步使用 gVisor 或 Kata。

需要联网的扩展能力通过显式权限和受控代理提供，不能让用户代码直接访问数据库、内部服务、宿主网络或云主机元数据。

### 9.8 输入与输出边界

容器目录建议分为：

```text
/bundle   只读执行包
/work     有容量限制的临时目录
/output   有类型和容量限制的输出目录
```

主服务只收集声明过的输出文件，并校验路径、大小和 MIME 类型。计算结果 HTML 同样属于不可信内容，应通过独立域名、无登录 Cookie、严格 CSP 和 sandboxed iframe 展示，避免结果页面攻击主站。

### 9.9 执行会话授权和缓存失败处理

`executionId` 必须在服务端关联：

- 用户 ID。
- 项目 ID、bundle hash 和解析后的 artifact hash。
- 容器租约 ID。
- 子进程 ID。
- 创建时间和过期时间。

继续、终止和读取结果时必须同时验证当前用户，不能只凭一个 `executionId` 操作执行会话。远程 sandbox 服务应只位于内部网络，并使用服务身份认证。

缓存写入和回收还必须满足：

- hash、文件清单或安全解压校验失败时删除临时内容，不能发布缓存项。
- 未完成上传对执行请求不可见，重复上传同一 hash 必须幂等。
- 缓存 GC 使用容量上限和 LRU/TTL 策略，但不得删除正在被容器租约引用的 artifact。
- `prepare` 后 artifact 被 GC 回收时，`execute` 返回可重试的 cache miss，由主 API 重新补齐缺失项。
- artifact hash 不能绕过项目所有权、分享授权或依赖访问检查。

## 10. 前端发布状态提示

前端直接使用后端返回的 `CalcPublishState`，不自行比较时间戳或猜测版本状态。

计算书列表沿用现有 `version` 列：

- `unpublished`：版本显示为空，并显示“未发布”标识。
- `published`：显示 latest 版本，例如 `v1.2.1`，不显示警告。
- `unpublished_changes`：显示 latest 版本，并显示“有未发布修改”标识。
- `workspace_version_mismatch`：同时显示 workspace 对应版本和 latest 版本，并提示“工作区与当前发布版不一致”。

编辑器在顶部名称、保存和运行按钮附近显示相同状态。编辑器运行按钮执行 workspace；发布入口要求用户填写版本号，并在成功后刷新报告详情和列表状态。

普通查看器执行已发布版本，只显示本次实际执行的版本名，不显示 workspace 修改警告，避免让用户误以为正式执行使用了未发布内容。

## 11. 建议模块边界

可以按职责逐步形成以下服务：

```text
CalcProjectService
  管理项目元数据、workspace、latest 指针和分类

CalcVersionService
  发布、校验和读取不可变命名版本

CalcArtifactService
  生成规范化文件清单，保存和读取内容寻址 artifact

CalcDependencyService
  管理依赖别名、selector、权限和循环检测

CalcShareService
  创建、撤销和验证分享链接

CalcImportService
  安全导入分享版本和 .uzc 归档

ExecutionBundleBuilder
  解析 selector，生成 calcdeps 命名空间和 bundle manifest

SandboxArtifactCache
  校验、发布、组装和回收 sandbox 节点 artifact

SandboxOrchestrator
  管理容器租约、子进程、资源限制和执行会话
```

控制器只负责认证、DTO 转换和调用服务，不直接拼接文件路径、解压归档或操作容器。

## 12. 渐进式重构方向

该架构不要求一次性完成，可以按以下方向逐步演进：

1. 使用项目 OID 和 `workspace` 目录保存当前内容，解除展示名称和分类对文件路径的影响。
2. 在保存流程中生成 workspace artifact，并增加 `version/v_x_y_z`、`latestVersionId` 和 `latest.json`。
3. 增加发布、调整 latest、恢复 workspace 和前端发布状态接口。
4. 增加项目局部依赖别名、默认 selector、多版本声明和 `calcdeps` 命名空间构建，只允许引用已发布版本。
5. 实现 workspace/latest/version 三种执行来源、分层 bundle manifest、sandbox artifact cache 和缺失 artifact 传输协议。
6. 将 sandbox 改为容器内独立子进程，停止传递主机文件路径，并补充租约授权和缓存回收。
7. 在统一 artifact、权限和版本模型之上实现分享链接与 `.uzc` 导入。

## 13. 验收场景

实现时至少验证以下场景：

1. 新项目保存后只存在 workspace，`publishState` 为 `unpublished`；编辑器可以执行 workspace，正式执行、引用和分享均返回“尚未发布”。
2. 发布 `1.0.0` 后创建 `version/v_1_0_0`，`latestVersionId` 和 `latest.json` 指向该版本，状态变为 `published`；默认 import 和 `.latest` import 均解析到该版本。
3. 再次保存 workspace 后，latest 仍指向 `1.0.0`，状态变为 `unpublished_changes`；编辑器执行新 workspace，普通查看器和依赖方继续执行 `1.0.0`。
4. 发布 `1.1.0` 后自动提升 latest，状态恢复为 `published`；新建 bundle 解析到 `1.1.0`，已经生成的旧 bundle 保持不变。
5. 将 latest 回退到 `1.0.0` 时 workspace 保持 `1.1.0` 内容，状态变为 `workspace_version_mismatch`；`.latest` 使用 `1.0.0`，`.v_1_1_0` 仍可显式使用。
6. 从 `1.0.0` 恢复 workspace 时只替换 workspace；latest 保持当前指针，发布状态根据两个 content hash 重新计算。
7. `latest.json` 缺失、损坏或内容过期时，可以根据数据库中的 `latestVersionId` 重建，不影响版本解析的权威结果。
8. 分享 latest 时，分享记录固定创建瞬间的版本 ID 和 artifact hash；之后提升 latest 不改变已有分享内容。
9. 保存 workspace 只上传新的 workspace artifact；未变化的依赖 artifact 继续命中缓存，交互式 `continue` 不重新传输 bundle。

## 14. 总结

推荐架构可以概括为：

> 内部使用稳定项目 ID 分离保存可编辑 workspace、latest 发布指针和不可变命名版本；只有已发布版本可以被引用和分享；执行时将 workspace、latest 或明确版本解析为内容寻址 artifact，只向 sandbox 传递缓存未命中的内容，并在按用户、bundle 和镜像隔离的短期容器中运行独立子进程。

在这个模型中：

- 改名和移动分类不会影响物理文件或 import。
- 用户无需知道内部 OID 和真实路径。
- 同名计算书不会覆盖彼此。
- workspace 保存不会使其他项目的默认依赖静默变化。
- 默认引用可以跟随 `latest`，显式版本引用保持不可变，同一次执行也可以比较多个版本。
- 前端可以明确区分未发布、已发布、存在未发布修改和 workspace 与 latest 不一致。
- 分享和导入可以安全重建项目身份及依赖关系。
- 服务器不会把整个用户目录暴露给不可信代码。
- 容器销毁不会使镜像层和 sandbox artifact 缓存失效，同一内容不需要每次重新传输。
- 每次执行都可以追溯到确定的 bundle、artifact、依赖版本和运行镜像。
