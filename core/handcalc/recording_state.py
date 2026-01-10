"""记录状态管理器"""


class RecordingState:
    """管理 AST 插桩的记录开关状态"""

    def __init__(self) -> None:
        self._enabled: bool = True

    @property
    def enabled(self) -> bool:
        """返回当前是否启用记录"""
        return self._enabled

    def enable(self) -> None:
        """启用记录"""
        self._enabled = True

    def disable(self) -> None:
        """禁用记录"""
        self._enabled = False

    def reset(self) -> None:
        """重置为默认状态（启用）"""
        self._enabled = True
