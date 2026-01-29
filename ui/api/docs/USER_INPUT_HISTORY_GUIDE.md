# 用户输入历史和版本控制优化指南

## 📋 概述

本次优化在原有沙箱执行系统的基础上，实现了：

1. **类型安全的响应数据模型** - 替代 dict 硬编码查询
2. **完整的用户输入历史保存** - 每次用户交互都被记录
3. **灵活的缓存机制** - 下次执行时自动加载上次的输入
4. **版本控制系统** - 用户可发布版本快照，直接恢复完整结果
5. **多端点协作** - 新增 4 个 API 端点支持版本管理

## 🏗️ 架构概览

### 数据流向

```
用户执行计算
    ↓
检查缓存 (load_from_cache=true)
    ↓
加载历史输入 → InputCache
    ↓
执行函数，显示 UI
    ↓
用户提交输入
    ↓
保存输入历史 → UserInputHistory
    ↓
继续执行或完成
    ↓
[用户可选] 发布版本 → PublishedVersion
    ↓
[用户可选] 从版本恢复 → 直接返回结果
```

### 核心模块

```
app/model/calc_execution_response.py
  ├─ ExecutionStartResponse       # 启动响应
  ├─ ExecutionResumeResponse      # 继续响应
  ├─ ExecutionStatusResponse      # 状态响应
  └─ ExecutionHistoryResponse     # 历史响应

app/db/models/user_input_history.py
  ├─ UserInputHistory             # 用户输入历史
  ├─ PublishedVersion             # 已发布的版本
  └─ InputCache                   # 输入缓存

app/db/dao/user_input_history_dao.py
  ├─ UserInputHistoryDAO          # 历史数据访问
  ├─ PublishedVersionDAO          # 版本数据访问
  └─ InputCacheDAO                # 缓存数据访问

app/service/calc_execution_service.py
  ├─ start_execution()            # 启动，支持加载缓存
  ├─ resume_execution()           # 继续，自动保存输入
  ├─ complete_execution()         # 完成，保存最终结果
  ├─ get_execution_history()      # 获取历史
  ├─ publish_version()            # 发布版本
  ├─ get_published_versions()     # 获取版本列表
  └─ restore_from_version()       # 从版本恢复

app/controller/calc/calc_execution.py
  ├─ POST /v1/calc/execution/start              # 启动执行
  ├─ POST /v1/calc/execution/resume            # 继续执行
  ├─ GET  /v1/calc/execution/execution-history # 获取历史
  ├─ POST /v1/calc/execution/publish           # 发布版本
  ├─ GET  /v1/calc/execution/published-versions# 获取版本列表
  └─ POST /v1/calc/execution/restore-from-version # 从版本恢复
```

## 🔄 使用工作流

### 场景 1：用户第一次执行计算

```bash
# 1. 启动执行，不加载缓存
POST /v1/calc/execution/start
{
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "session_id": "sess_123",
    "params": {"x": 10},
    "load_from_cache": false
}

# 响应：显示第一个 UI
{
    "ok": true,
    "data": {
        "status": "waiting_ui",
        "session_id": "sess_123",
        "cached": false,
        "ui": {
            "title": "输入参数",
            "fields": [
                {
                    "name": "a",
                    "type": "number",
                    "label": "参数 A"
                }
            ]
        }
    }
}

# 2. 用户填完表单，继续执行
POST /v1/calc/execution/resume
{
    "session_id": "sess_123",
    "user_input": {"a": 5},
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "step_number": 1,
    "total_steps": 3
}

# 响应：显示下一个 UI 或完成
{
    "ok": true,
    "data": {
        "status": "completed",
        "session_id": "sess_123",
        "result": "<html>...</html>"
    }
}
```

### 场景 2：用户第二次执行，使用缓存

```bash
# 启动执行，加载上次的缓存输入
POST /v1/calc/execution/start
{
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "session_id": "sess_456",
    "params": {},
    "load_from_cache": true  # 关键！
}

# 响应：自动应用缓存，继续从上次的地方开始
{
    "ok": true,
    "data": {
        "status": "waiting_ui",
        "session_id": "sess_456",
        "cached": true,  # 表示使用了缓存
        "ui": {
            "title": "输入参数",
            "fields": [
                {
                    "name": "a",
                    "type": "number",
                    "label": "参数 A",
                    "default": 5  # 使用上次的值
                }
            ]
        }
    }
}
```

### 场景 3：用户发布版本，稍后快速恢复

```bash
# 1. 执行完成后，发布版本
POST /v1/calc/execution/publish
{
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "version_name": "最终版本",
    "description": "经过最终审核的计算结果"
}

# 响应
{
    "ok": true,
    "data": {
        "version_id": 1,
        "version_name": "最终版本",
        "version_number": 1,
        "published_at": "2026-01-29T10:00:00"
    }
}

# 2. 获取用户的所有已发布版本
GET /v1/calc/execution/published-versions?file_path=examples/calc.py&func_name=calculate

# 响应
{
    "ok": true,
    "data": [
        {
            "version_id": 1,
            "version_name": "最终版本",
            "version_number": 1,
            "published_at": "2026-01-29T10:00:00",
            "use_count": 2,
            "total_steps": 3
        }
    ]
}

# 3. 用户选择版本，直接获取结果（无需输入过程！）
POST /v1/calc/execution/restore-from-version
{
    "version_id": 1
}

# 响应：立即返回完整结果
{
    "ok": true,
    "data": {
        "status": "completed",
        "version_id": 1,
        "version_name": "最终版本",
        "result": "<html>...完整的计算结果...</html>",
        "steps": 3,
        "restored_at": "2026-01-29T14:00:00"
    }
}
```

## 💾 数据库模型详解

### UserInputHistory（用户输入历史）

```python
{
    "id": 1,
    "user_id": "user_123",
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "session_id": "sess_123",
    "input_history": [
        {
            "step_number": 1,
            "field_values": {"a": 5, "b": 10},
            "timestamp": "2026-01-29T10:00:00"
        },
        {
            "step_number": 2,
            "field_values": {"method": "fast"},
            "timestamp": "2026-01-29T10:00:05"
        }
    ],
    "current_step": 2,
    "total_steps": 3,
    "final_result": "<html>...</html>",
    "final_result_hash": "abc123...",
    "is_complete": true,
    "is_draft": true,  # 尚未发布
    "execution_time": 1234,  # 毫秒
    "created_at": "2026-01-29T10:00:00",
    "updated_at": "2026-01-29T10:00:10"
}
```

### PublishedVersion（已发布版本）

```python
{
    "id": 1,
    "user_id": "user_123",
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "version_name": "最终版本",
    "version_number": 1,
    "version_description": "经过最终审核的计算结果",
    "input_history": [  # 完整的输入历史快照
        {
            "step_number": 1,
            "field_values": {"a": 5, "b": 10},
            "timestamp": "2026-01-29T10:00:00"
        },
        ...
    ],
    "final_result": "<html>...</html>",
    "final_result_hash": "abc123...",
    "total_steps": 3,
    "execution_time": 1234,
    "published_at": "2026-01-29T10:00:10",
    "use_count": 2,  # 被恢复了 2 次
    "is_public": false
}
```

### InputCache（输入缓存）

```python
{
    "id": 1,
    "user_id": "user_123",
    "file_path": "examples/calc.py",
    "func_name": "calculate",
    "cached_input": {
        "a": 5,
        "b": 10,
        "method": "fast"
    },
    "total_steps": 3,
    "completed_steps": 2,
    "updated_at": "2026-01-29T10:00:10",
    "expires_at": "2026-02-01T10:00:10"  # 72 小时过期
}
```

## 🔌 API 端点详解

### 1. POST /start - 启动执行

**新增参数：**
- `load_from_cache` (bool, default=true) - 是否加载缓存

**新增返回字段：**
- `cached` (bool) - 是否使用了缓存

**工作流：**
1. 如果 `load_from_cache=true`，检查 InputCache
2. 如果缓存存在且有效，应用缓存数据
3. 调用沙箱执行函数
4. 返回首个 UI 或完整结果

### 2. POST /resume - 继续执行

**新增参数：**
- `file_path` (str) - 用于保存到数据库
- `func_name` (str) - 用于保存到数据库
- `step_number` (int) - 当前步骤号
- `total_steps` (int) - 总步骤数

**自动保存逻辑：**
1. 接收用户输入
2. 调用沙箱继续执行
3. 保存输入到 UserInputHistory
4. 如果执行完成，更新缓存

### 3. GET /execution-history - 获取执行历史

**返回字段：**
```json
{
    "file_path": "...",
    "func_name": "...",
    "last_execution_at": "...",
    "input_history": [...],
    "published_versions": [...],
    "completion_percentage": 100.0,
    "total_executions": 3
}
```

### 4. POST /publish - 发布版本

**参数：**
- `file_path` (str)
- `func_name` (str)
- `version_name` (str) - 用户可读的版本名，如 "初版"、"v1.0"
- `description` (str, optional)

**自动操作：**
1. 获取最新的完成执行记录
2. 保存输入历史快照到 PublishedVersion
3. 保存最终结果快照
4. 标记原记录为已发布

### 5. GET /published-versions - 获取版本列表

**返回：** 用户该函数的所有已发布版本列表

### 6. POST /restore-from-version - 从版本恢复

**核心优势：** 直接返回完整结果，无需用户输入！

**参数：**
- `version_id` (int) - 已发布版本的 ID

**工作流：**
1. 查询 PublishedVersion 数据
2. 增加该版本的 use_count
3. 直接返回 final_result
4. **无需调用沙箱执行！**

## 📊 性能考虑

### 缓存策略

- **默认过期时间：** 72 小时
- **自动清理：** 后台任务定期删除过期缓存
- **缓存键：** `{user_id}:{file_path}:{func_name}`

### 数据库索引

已创建以下索引加速查询：
```python
Index('idx_user_file_func', 'user_id', 'file_path', 'func_name')
Index('idx_user_created_at', 'user_id', 'created_at')
Index('idx_cache_user_file', 'user_id', 'file_path', 'func_name')
Index('idx_file_version', 'file_path', 'func_name', 'version_number')
```

### 存储优化

- **input_history** 存储为 JSON 数组
- **final_result_hash** 用于快速去重检测
- **完整结果** 仅保存一次（在 PublishedVersion 中）

## 🔒 数据安全性

### 用户隔离

所有查询都包含 `user_id` 条件：
```python
await UserInputHistoryDAO.get_execution_history(
    session,
    user_id=str(tokenPayloads.id),  # 确保用户隔离
    file_path=file_path,
    func_name=func_name,
)
```

### 版本控制

- 版本只能由原所有者发布
- 版本只能由原所有者恢复
- `PublishedVersion.user_id` 检查确保所有权

## 🧪 集成示例

### Python 客户端示例

```python
import httpx
from datetime import datetime

class UzonCalcClient:
    def __init__(self, api_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    async def start_execution(
        self,
        file_path: str,
        func_name: str,
        params: dict,
        load_from_cache: bool = True
    ) -> dict:
        """启动计算，支持从缓存加载"""
        response = await self.client.post(
            "/v1/calc/execution/start",
            params={
                "file_path": file_path,
                "func_name": func_name,
                "session_id": f"sess_{datetime.now().timestamp()}",
                "load_from_cache": load_from_cache,
            },
            json={"params": params}
        )
        return response.json()
    
    async def get_execution_history(
        self,
        file_path: str,
        func_name: str
    ) -> dict:
        """获取执行历史和已发布版本"""
        response = await self.client.get(
            "/v1/calc/execution/execution-history",
            params={
                "file_path": file_path,
                "func_name": func_name,
            }
        )
        return response.json()
    
    async def restore_version(self, version_id: int) -> dict:
        """快速恢复已发布版本的结果"""
        response = await self.client.post(
            "/v1/calc/execution/restore-from-version",
            json={"version_id": version_id}
        )
        return response.json()
```

### Vue.js 前端示例

```javascript
// 加载缓存执行
const startWithCache = async () => {
    const response = await fetch('/v1/calc/execution/start', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            file_path: 'examples/calc.py',
            func_name: 'calculate',
            session_id: `sess_${Date.now()}`,
            load_from_cache: true  // 加载缓存！
        })
    });
    
    const data = await response.json();
    if (data.data.cached) {
        // 缓存已应用，表单会显示上次的值
        console.log('缓存的输入已加载');
    }
    return data.data;
};

// 发布版本
const publishVersion = async (filePath, funcName, versionName) => {
    const response = await fetch('/v1/calc/execution/publish', {
        method: 'POST',
        body: JSON.stringify({
            file_path: filePath,
            func_name: funcName,
            version_name: versionName,
            description: `版本发布于 ${new Date().toLocaleString()}`
        })
    });
    return await response.json();
};

// 从版本快速恢复
const restoreVersion = async (versionId) => {
    const response = await fetch(
        '/v1/calc/execution/restore-from-version',
        {
            method: 'POST',
            body: JSON.stringify({ version_id: versionId })
        }
    );
    
    const data = await response.json();
    // 直接显示完整结果，无需用户输入！
    displayResult(data.data.result);
};
```

## 📝 数据库迁移

创建新的数据库表：

```sql
-- 用户输入历史表
CREATE TABLE user_input_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(256) NOT NULL,
    func_name VARCHAR(128) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    input_history JSON DEFAULT '[]',
    current_step INT DEFAULT 0,
    total_steps INT DEFAULT 0,
    final_result TEXT,
    final_result_hash VARCHAR(64),
    is_complete BOOLEAN DEFAULT FALSE,
    is_draft BOOLEAN DEFAULT TRUE,
    draft_version_id INT,
    parameters JSON,
    execution_time INT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,
    UNIQUE KEY uq_user_execution (user_id, file_path, func_name, session_id),
    INDEX idx_user_file_func (user_id, file_path, func_name),
    INDEX idx_user_created_at (user_id, created_at)
);

-- 已发布版本表
CREATE TABLE published_version (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(256) NOT NULL,
    func_name VARCHAR(128) NOT NULL,
    version_name VARCHAR(128) NOT NULL,
    version_number INT DEFAULT 1,
    version_description TEXT,
    input_history JSON NOT NULL,
    final_result LONGTEXT NOT NULL,
    final_result_hash VARCHAR(64) NOT NULL,
    parameters JSON,
    total_steps INT NOT NULL,
    execution_time INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_from_history_id INT,
    download_count INT DEFAULT 0,
    use_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    INDEX idx_user_published (user_id, published_at),
    INDEX idx_file_version (file_path, func_name, version_number)
);

-- 输入缓存表
CREATE TABLE input_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(256) NOT NULL,
    func_name VARCHAR(128) NOT NULL,
    cached_input JSON NOT NULL,
    input_history_id INT NOT NULL,
    total_steps INT NOT NULL,
    completed_steps INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at DATETIME,
    INDEX idx_cache_user_file (user_id, file_path, func_name)
);
```

## 🎯 总结

这次优化提供了：

| 特性 | 好处 |
|------|------|
| **类型安全的响应** | 减少 dict 查询错误，增强代码可维护性 |
| **自动输入保存** | 用户无需手动保存，每次交互都被记录 |
| **缓存加载** | 下次执行自动填充上次的值，提升用户体验 |
| **版本发布** | 完整的执行快照可被保存和重复使用 |
| **快速恢复** | 从版本直接获取结果，无需重新执行 |
| **完整的历史记录** | 用户可查看和管理所有执行历史 |

这使 UzonCalc 的计算工作流变得更加高效和用户友好！
