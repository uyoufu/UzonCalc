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

        # 是否启用 fstring 方程渲染
        # 默认为 False
        # 若启用, 则会将 fstring 中的表达式提取出来进行方程渲染
        # 例如: f"{a+b}" 会被渲染为 "a + b = 3"
        self.enable_fstring_equation: bool = False

        # 跳过以 _ 开头的临时/私有变量的记录
        self.suppress_private_assignments: bool = suppress_private_assignments

        # 记录结构化步骤（不仅是字符串），便于后续渲染或调试
        self.record_structured_steps: bool = record_structured_steps

        # 是否跳过内容记录
        # 若为 True，则不会记录内容到 ctx.contents 中
        # 逻辑在两个地方实现
        # 1. 在 AST 解析时，遇到 hide() 时，将不会继续解析
        # 2. CalcContext.append_content 方法中进行检查
        self.skip_content: bool = False

        # 别名映射
        self.aliases: dict[str, str] = {}

        # 自定义的后处理器列表
        self.post_handlers: list[BasePostHandler] = get_default_post_handlers()

        # 页面标题
        self.page_title: str = "UzonCalc Calculation Sheet"

        # 页面大小，支持: A4, A3, A5, Letter, Legal
        self.page_size: str = "A4"

        # 自定义样式字典，格式为 {选择器: {属性: 值}}
        # 例如: {"body": {"font_size": "14px", "line_height": "1.8"}}
        self.styles: dict[str, dict] = {}
