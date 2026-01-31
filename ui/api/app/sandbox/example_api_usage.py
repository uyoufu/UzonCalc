"""
API 端使用 Sandbox 执行器的示例

演示如何在 API 中使用 CalcSandboxExecutor 来：
1. 加载并执行用户的计算函数
2. 处理 UI 交互（暂停/恢复）
3. 管理多个并发会话
"""

import asyncio
import sys
from pathlib import Path

# 确保可以导入 sandbox 模块
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from app.sandbox.executor import CalcSandboxExecutor
from app.sandbox.generator_manager import ExecutionStatus


async def demo_api_execution():
    """演示完整的 API 执行流程"""
    
    # 1. 初始化执行器
    executor = CalcSandboxExecutor(
        safe_dirs=["d:\\Develop\\Personal\\UzonCalc\\tests"],  # 白名单
        session_timeout=3600
    )
    await executor.initialize()
    
    try:
        print("=" * 60)
        print("场景 1: 执行带 UI 交互的计算函数")
        print("=" * 60)
        
        # 2. 启动执行
        session_id = "test-session-001"
        file_path = "d:\\Develop\\Personal\\UzonCalc\\tests\\example.py"
        func_name = "sheet"
        params = {}
        
        print(f"启动执行: {func_name}")
        status, ui, html = await executor.execute_function(
            file_path=file_path,
            func_name=func_name,
            session_id=session_id,
            params=params
        )
        
        print(f"状态: {status.value}")
        
        # 3. 处理 UI 交互循环
        step = 1
        while status == ExecutionStatus.WAITING_INPUT and ui is not None:
            print(f"\n--- 步骤 {step}: 等待用户输入 ---")
            print(f"UI 标题: {ui.get('title')}")
            print(f"字段: {[f['name'] for f in ui.get('fields', [])]}")
            
            # 模拟用户输入（在实际 API 中，这会来自前端）
            if step == 1:
                user_input = {"field1": 100, "field2": 200}
            else:
                user_input = {"confirm": True}
            
            print(f"用户输入: {user_input}")
            
            # 4. 恢复执行
            status, ui, html = await executor.resume_execution(
                session_id=session_id,
                user_input=user_input
            )
            
            print(f"新状态: {status.value}")
            step += 1
        
        # 5. 执行完成
        if status == ExecutionStatus.COMPLETED:
            print(f"\n✓ 执行完成")
            print(f"HTML 输出长度: {len(html)} 字符")
            print(f"HTML 预览: {html[:200]}..." if len(html) > 200 else f"HTML: {html}")
        else:
            print(f"\n✗ 执行失败: {status.value}")
        
        print("\n" + "=" * 60)
        print("场景 2: 执行无 UI 交互的函数（同步）")
        print("=" * 60)
        
        session_id_2 = "test-session-002"
        func_name_2 = "sync_sheet"
        
        print(f"启动执行: {func_name_2}")
        status2, ui2, html2 = await executor.execute_function(
            file_path=file_path,
            func_name=func_name_2,
            session_id=session_id_2,
            params=params
        )
        
        print(f"状态: {status2.value}")
        
        if status2 == ExecutionStatus.WAITING_INPUT and ui2 is not None:
            # 自动使用默认值
            print("遇到 UI，使用默认值...")
            default_input = {field["name"]: field.get("default") for field in ui2.get("fields", [])}
            status2, ui2, html2 = await executor.resume_execution(
                session_id=session_id_2,
                user_input=default_input
            )
        
        if status2 == ExecutionStatus.COMPLETED:
            print(f"✓ 执行完成")
        
        print("\n" + "=" * 60)
        print("场景 3: 查看会话状态")
        print("=" * 60)
        
        # 获取所有会话
        all_sessions = executor.get_all_sessions()
        print(f"活跃会话数: {len(all_sessions)}")
        for sess in all_sessions:
            print(f"  - {sess['session_id']}: {sess['status']}, UI步骤: {sess['ui_steps']}")
        
        # 获取缓存信息
        cache_info = executor.get_cache_info()
        print(f"\n缓存模块数: {cache_info['cached_modules']}")
        
        print("\n" + "=" * 60)
        print("场景 4: 取消执行")
        print("=" * 60)
        
        # 启动一个新会话
        session_id_3 = "test-session-003"
        print(f"启动新会话: {session_id_3}")
        status3, ui3, html3 = await executor.execute_function(
            file_path=file_path,
            func_name=func_name,
            session_id=session_id_3,
            params=params
        )
        
        print(f"状态: {status3.value}")
        
        # 立即取消
        print("取消执行...")
        executor.cancel_execution(session_id_3)
        
        # 尝试获取状态（应该返回 None）
        info = executor.get_session_status(session_id_3)
        print(f"会话状态: {info}")
        
    finally:
        # 清理
        await executor.shutdown()
        print("\n执行器已关闭")


async def demo_concurrent_sessions():
    """演示并发会话管理"""
    
    print("\n" + "=" * 60)
    print("场景 5: 并发执行多个会话")
    print("=" * 60)
    
    executor = CalcSandboxExecutor()
    await executor.initialize()
    
    try:
        file_path = "d:\\Develop\\Personal\\UzonCalc\\tests\\example.py"
        func_name = "sheet"
        
        # 启动多个会话
        tasks = []
        for i in range(3):
            session_id = f"concurrent-{i}"
            print(f"启动会话 {session_id}")
            task = executor.execute_function(
                file_path=file_path,
                func_name=func_name,
                session_id=session_id,
                params={}
            )
            tasks.append((session_id, task))
        
        # 等待所有会话的第一步完成
        results = await asyncio.gather(*[t[1] for t in tasks])
        
        print(f"\n所有会话已启动:")
        for (session_id, _), (status, ui, html) in zip(tasks, results):
            print(f"  {session_id}: {status.value}")
        
        # 查看活跃会话
        all_sessions = executor.get_all_sessions()
        print(f"\n当前活跃会话: {len(all_sessions)}")
        
    finally:
        await executor.shutdown()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_api_execution())
    asyncio.run(demo_concurrent_sessions())
    
    print("\n" + "=" * 60)
    print("所有 API 示例执行完成！")
    print("=" * 60)
