"""
实现示例

展示如何在实际项目中集成沙箱执行系统。
"""

# ============================================================================
# 示例 1: 在 FastAPI 应用中集成 (开发环境)
# ============================================================================

"""
# main.py

from fastapi import FastAPI
from app.sandbox.integration import initialize_sandbox, shutdown_sandbox, SandboxConfig
from app.controller.calc.calc_execution import router as execution_router

app = FastAPI(title="UzonCalc API")

# 注册路由
app.include_router(execution_router)

@app.on_event("startup")
async def startup():
    # 初始化沙箱 (本地模式)
    config = SandboxConfig(
        mode="local",
        safe_dirs=[
            "/path/to/calc/files",
            "/tmp/calc"
        ],
        session_timeout=3600,
    )
    await initialize_sandbox(config)

@app.on_event("shutdown")
async def shutdown():
    await shutdown_sandbox()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""


# ============================================================================
# 示例 2: 从环境变量配置 (生产环境)
# ============================================================================

"""
# main.py

from fastapi import FastAPI
from app.sandbox.integration import initialize_sandbox, shutdown_sandbox, config_from_env
from app.controller.calc.calc_execution import router as execution_router

app = FastAPI(title="UzonCalc API")
app.include_router(execution_router)

@app.on_event("startup")
async def startup():
    # 从环境变量读取配置
    config = config_from_env()
    await initialize_sandbox(config)

@app.on_event("shutdown")
async def shutdown():
    await shutdown_sandbox()
"""


# ============================================================================
# 示例 3: 远程沙箱模式
# ============================================================================

"""
# main.py

from fastapi import FastAPI
from app.sandbox.integration import initialize_sandbox, shutdown_sandbox, create_remote_sandbox_config
from app.controller.calc.calc_execution import router as execution_router

app = FastAPI(title="UzonCalc API")
app.include_router(execution_router)

@app.on_event("startup")
async def startup():
    # 连接到远程沙箱容器
    config = create_remote_sandbox_config(
        sandbox_url="http://sandbox-container:3346"
    )
    await initialize_sandbox(config)

@app.on_event("shutdown")
async def shutdown():
    await shutdown_sandbox()
"""


# ============================================================================
# 示例 4: UzonCalc 计算代码
# ============================================================================

"""
# /path/to/calc/files/example.py

from uzoncalc import *

@uzon_calc()
async def sheet(ctx=None):
    '''
    示例计算函数，展示 UI 交互
    '''
    
    doc_title("计算示例")
    H1("钢梁设计计算")
    
    # 第一个 UI: 输入参数
    input_data = await UI(Window(
        title="输入梁的基本参数",
        fields=[
            Field("beam_length", "number", "梁长 (m)", default=10),
            Field("load_type", "select", "荷载类型", 
                  options=["均布荷载", "集中荷载"]),
        ]
    ))
    
    beam_length = input_data["beam_length"]
    load_type = input_data["load_type"]
    
    # 执行计算
    moment = beam_length ** 2 / 8  # 简化计算
    
    # 中间结果
    H2("计算结果")
    f"梁长: {beam_length} m"
    f"弯矩: {moment} kN·m"
    
    # 第二个 UI: 根据第一个结果确定材料
    if load_type == "均布荷载":
        material_data = await UI(Window(
            title="选择梁材料",
            fields=[
                Field("material", "select", "材料",
                      options=["Q235", "Q345", "Q390"]),
                Field("safety_factor", "number", "安全系数", default=1.5),
            ]
        ))
        
        material = material_data["material"]
        safety_factor = material_data["safety_factor"]
        
        # 继续计算
        design_moment = moment * safety_factor
        
        H2("设计结果")
        f"设计弯矩: {design_moment} kN·m"
        f"选用材料: {material}"
    
    save()
"""


# ============================================================================
# 示例 5: 前端调用 (Vue.js)
# ============================================================================

"""
// src/pages/calcReport/viewer/useCalcExecution.ts

import { ref } from 'vue'
import axios from 'axios'

export function useCalcExecution() {
  const sessionId = ref('')
  const currentUI = ref(null)
  const resultHTML = ref('')
  const isLoading = ref(false)
  const error = ref('')

  /**
   * 启动计算
   */
  async function startExecution(
    filePath: string,
    funcName: string,
    initialParams: Record<string, any>
  ) {
    isLoading.value = true
    error.value = ''
    sessionId.value = `session_${Date.now()}`

    try {
      const response = await axios.post(
        '/api/v1/calc/execution/start',
        {
          file_path: filePath,
          func_name: funcName,
          session_id: sessionId.value,
          params: initialParams,
        }
      )

      const result = response.data.data

      if (result.status === 'waiting_ui') {
        // 有 UI 需要用户输入
        currentUI.value = result.ui
      } else if (result.status === 'completed') {
        // 直接完成，无需 UI
        resultHTML.value = result.result
        currentUI.value = null
      } else if (result.status === 'error') {
        error.value = result.error
      }
    } catch (err) {
      error.value = (err as any).message
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 提交 UI 表单，继续执行
   */
  async function submitUIForm(formData: Record<string, any>) {
    isLoading.value = true
    error.value = ''

    try {
      const response = await axios.post(
        '/api/v1/calc/execution/resume',
        {
          session_id: sessionId.value,
          user_input: formData,
        }
      )

      const result = response.data.data

      if (result.status === 'waiting_ui') {
        // 还有下一个 UI
        currentUI.value = result.ui
      } else if (result.status === 'completed') {
        // 计算完成
        resultHTML.value = result.result
        currentUI.value = null
      } else if (result.status === 'error') {
        error.value = result.error
      }
    } catch (err) {
      error.value = (err as any).message
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 取消执行
   */
  async function cancelExecution() {
    try {
      await axios.post(
        '/api/v1/calc/execution/cancel',
        {
          session_id: sessionId.value,
        }
      )
      currentUI.value = null
      resultHTML.value = ''
    } catch (err) {
      error.value = (err as any).message
    }
  }

  return {
    sessionId,
    currentUI,
    resultHTML,
    isLoading,
    error,
    startExecution,
    submitUIForm,
    cancelExecution,
  }
}

// 在组件中使用：
// <script lang="ts" setup>
// const { currentUI, startExecution, submitUIForm } = useCalcExecution()
//
// async function handleStart() {
//   await startExecution(
//     '/path/to/calc.py',
//     'sheet',
//     { initial_param: 100 }
//   )
// }
//
// async function handleUISubmit(formData) {
//   await submitUIForm(formData)
// }
// </script>
"""


# ============================================================================
# 示例 6: Docker 部署
# ============================================================================

"""
# Dockerfile.api (API 服务器)

FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 本地模式
ENV SANDBOX_MODE=local
ENV SANDBOX_SAFE_DIRS=/calc/files

# 或者远程模式
# ENV SANDBOX_MODE=remote
# ENV SANDBOX_URL=http://sandbox:3346

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
"""

"""
# Dockerfile.sandbox (沙箱服务)

FROM python:3.11

WORKDIR /app

COPY requirements-sandbox.txt .
RUN pip install -r requirements-sandbox.txt

COPY sandbox_service.py .
COPY app/sandbox app/sandbox
COPY uzoncalc uzoncalc

ENV SAFE_DIRS=/calc/files

EXPOSE 3346

CMD ["python", "sandbox_service.py"]
"""

"""
# docker-compose.yml

version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      SANDBOX_MODE: remote
      SANDBOX_URL: http://sandbox:3346
    depends_on:
      - sandbox
    networks:
      - calc-network

  sandbox:
    build:
      context: .
      dockerfile: Dockerfile.sandbox
    ports:
      - "3346:3346"
    volumes:
      - ./calc-files:/calc/files
    environment:
      SAFE_DIRS: /calc/files
    networks:
      - calc-network

networks:
  calc-network:
    driver: bridge
"""


# ============================================================================
# 示例 7: 单元测试
# ============================================================================

"""
# tests/test_calc_execution.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.sandbox.integration import initialize_sandbox, shutdown_sandbox, SandboxConfig

client = TestClient(app)

@pytest.fixture(scope="module")
async def setup_sandbox():
    # 启动沙箱
    config = SandboxConfig(
        mode="local",
        safe_dirs=["./tests/calc_files"],
    )
    await initialize_sandbox(config)
    yield
    await shutdown_sandbox()

def test_simple_execution(setup_sandbox):
    response = client.post(
        "/api/v1/calc/execution/start",
        json={
            "file_path": "./tests/calc_files/simple.py",
            "func_name": "sheet",
            "session_id": "test_001",
            "params": {},
        }
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] in ["waiting_ui", "completed", "error"]

def test_ui_interaction(setup_sandbox):
    # 第一步：启动执行
    response1 = client.post(
        "/api/v1/calc/execution/start",
        json={
            "file_path": "./tests/calc_files/with_ui.py",
            "func_name": "sheet",
            "session_id": "test_002",
            "params": {},
        }
    )
    assert response1.status_code == 200
    data1 = response1.json()["data"]
    assert data1["status"] == "waiting_ui"

    # 第二步：提交 UI 表单
    session_id = data1["session_id"]
    response2 = client.post(
        "/api/v1/calc/execution/resume",
        json={
            "session_id": session_id,
            "user_input": {"value": 100},
        }
    )
    assert response2.status_code == 200
    data2 = response2.json()["data"]
    assert data2["status"] in ["waiting_ui", "completed"]
"""


# ============================================================================
# 示例 8: 错误处理
# ============================================================================

"""
# 在应用中处理错误

# API 响应错误示例
{
    "ok": false,
    "message": "执行失败",
    "data": {
        "status": "error",
        "session_id": "abc123",
        "error": "FileNotFoundError: /calc/files/example.py not found"
    }
}

# 前端处理
async function startCalculation(file, func, params) {
    try {
        const response = await axios.post('/api/v1/calc/execution/start', {
            file_path: file,
            func_name: func,
            session_id: generateSessionId(),
            params: params,
        })
        
        if (!response.data.ok) {
            showError(response.data.message)
            return
        }
        
        const result = response.data.data
        if (result.status === 'error') {
            showError(result.error)
        } else if (result.status === 'waiting_ui') {
            showUIDialog(result.ui)
        }
    } catch (error) {
        showError('网络错误: ' + error.message)
    }
}
"""
