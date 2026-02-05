"""
桌面模式专用 API 控制器
"""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
import tkinter as tk
from tkinter import filedialog

from app.response.response_result import ResponseResult, ok
from config import app_config

router = APIRouter(
    prefix="/v1/desktop",
    tags=["desktop"],
)


def _show_file_dialog():
    """
    在线程池中运行的同步函数，用于弹出文件对话框
    """

    # 显示声明 tkinter 的根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes("-topmost", True)  # 确保窗口在最前端

    file_path = filedialog.askopenfilename()

    root.destroy()
    return file_path


@router.get("/select-file")
async def select_local_file() -> ResponseResult[str]:
    """
    弹出文件选择对话框并返回选择的文件路径（仅限桌面模式）
    """
    if not app_config.is_desktop:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in desktop mode",
        )

    try:
        # 使用 run_in_threadpool 避免阻塞 FastAPI 事件循环
        file_path = await run_in_threadpool(_show_file_dialog)
        return ok(file_path if file_path else "")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to open file dialog: {str(e)}",
        )
