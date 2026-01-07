from core.handcalc.post_handlers.base_post_handler import BasePostHandler
from core.handcalc.post_handlers.post_pipeline import get_default_post_handlers


class ContextOptions:
    def __init__(
        self,
        *,
        enable_debug: bool = False,
        enable_substitution: bool = True,
        suppress_private_assignments: bool = True,
        record_structured_steps: bool = True
    ):
        # 是否启用调试模式，记录更多步骤信息
        self.enable_debug: bool = enable_debug

        # 在方程中将变量替换为实际值
        # 如 a = b + c, 为 true 时，会显示为 a = b + c = 1+2=3
        # 否则显示 a = b + c = 3
        self.enable_substitution: bool = enable_substitution

        # 跳过以 _ 开头的临时/私有变量的记录
        self.suppress_private_assignments: bool = suppress_private_assignments

        # 记录结构化步骤（不仅是字符串），便于后续渲染或调试
        self.record_structured_steps: bool = record_structured_steps

        # 是否跳过内容记录
        # 若为 True，则不会记录内容到 ctx.contents 中
        # 逻辑在 CalcContext.append_content 方法中实现
        self.skip_content: bool = False

        # 别名映射
        self.aliases: dict[str, str] = {}

        # 自定义的后处理器列表
        self.post_handlers: list[BasePostHandler] = get_default_post_handlers()
