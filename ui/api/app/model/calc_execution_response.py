"""
计算执行响应数据模型

定义所有计算执行相关的响应类型，替代 dict 硬编码。
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Any, Dict
from datetime import datetime
from uzoncalc import *

@dataclass
class UIField:
    """UI 字段定义"""
    name: str
    type: str  # 'text', 'number', 'select', 'checkbox', 'textarea', etc.
    label: Optional[str] = None
    default: Optional[Any] = None
    options: Optional[List[Dict[str, Any]]] = None  # For select, radio, checkbox
    required: bool = False
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UIWindow:
    """UI 窗口定义"""
    title: str
    fields: List[UIField]
    description: Optional[str] = None
    layout: str = "vertical"  # 'vertical', 'horizontal', 'grid'
    submit_label: str = "提交"
    cancel_label: str = "取消"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "layout": self.layout,
            "submit_label": self.submit_label,
            "cancel_label": self.cancel_label,
        }


@dataclass
class ExecutionStartResponse:
    """启动执行的响应"""
    status: str  # 'waiting_ui', 'completed', 'error'
    session_id: str
    ui: Optional[UIWindow] = None
    result: Optional[str] = None  # HTML 结果
    error: Optional[str] = None
    error_type: Optional[str] = None
    ui_steps: int = 0
    cached: bool = False  # 是否使用了缓存的输入

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "status": self.status,
            "session_id": self.session_id,
            "ui_steps": self.ui_steps,
            "cached": self.cached,
        }
        
        if self.ui is not None:
            result["ui"] = self.ui.to_dict()
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
            result["error_type"] = self.error_type

        return result


@dataclass
class ExecutionResumeResponse:
    """继续执行的响应"""
    status: str  # 'waiting_ui', 'completed', 'error'
    session_id: str
    ui: Optional[UIWindow] = None
    result: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    ui_steps: int = 0
    saved: bool = False  # 是否已保存用户输入

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "status": self.status,
            "session_id": self.session_id,
            "ui_steps": self.ui_steps,
            "saved": self.saved,
        }
        
        if self.ui is not None:
            result["ui"] = self.ui.to_dict()
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
            result["error_type"] = self.error_type

        return result


@dataclass
class ExecutionStatusResponse:
    """执行状态响应"""
    session_id: str
    status: str  # 'idle', 'running', 'waiting_ui', 'completed', 'error', 'cancelled'
    ui_steps: int
    has_error: bool
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "ui_steps": self.ui_steps,
            "has_error": self.has_error,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


@dataclass
class SessionInfo:
    """执行会话信息"""
    session_id: str
    status: str
    created_at: datetime
    last_activity: datetime
    ui_steps: int
    has_error: bool
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    func_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ui_steps": self.ui_steps,
            "has_error": self.has_error,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "func_name": self.func_name,
        }


@dataclass
class InputHistoryItem:
    """输入历史项"""
    step_number: int
    field_values: Dict[str, Any]
    timestamp: datetime
    is_version: bool = False
    version_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_number": self.step_number,
            "field_values": self.field_values,
            "timestamp": self.timestamp.isoformat(),
            "is_version": self.is_version,
            "version_name": self.version_name,
        }


@dataclass
class ExecutionHistoryResponse:
    """执行历史响应"""
    file_path: str
    func_name: str
    last_execution_at: datetime
    input_history: List[InputHistoryItem]
    published_versions: List[Dict[str, Any]] = field(default_factory=list)
    completion_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "func_name": self.func_name,
            "last_execution_at": self.last_execution_at.isoformat(),
            "input_history": [item.to_dict() for item in self.input_history],
            "published_versions": self.published_versions,
            "completion_percentage": self.completion_percentage,
        }
