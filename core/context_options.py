from core.handcalc.post_handlers.base_post_handler import BasePostHandler
from core.handcalc.post_handlers.post_pipeline import get_default_post_handlers


class PageInfo:
    font_family: str = "仿宋, Arial, sans-serif"

    # A3, A4, A5, Letter, etc.
    size: str = "A4"
    # units: mm
    margin: str = "20mm"

    # region 页眉页脚
    header_left: str = "1"
    header_center: str = "2"
    header_right: str = "3"

    footer_left: str = "4"
    footer_center: str = "5"
    footer_right: str = "6"

    header: str = ""
    footer: str = ""
    # endregion

    def _get_x_margin_expression(self) -> str:
        """获取 x 方向边距表达式（不包含 calc 包装）"""
        parts = self.margin.split()

        if len(parts) == 1:
            return f"{parts[0]} * 2"
        elif len(parts) == 2:
            return f"{parts[1]} * 2"
        elif len(parts) == 3:
            return f"{parts[1]} * 2"
        elif len(parts) == 4:
            return f"{parts[1]} + {parts[3]}"
        else:
            return f"{self.margin} * 2"

    def get_page_size_dimensions(self) -> tuple[str, str]:
        """
        根据页面尺寸名称返回对应的宽度和高度

        Returns:
            (page_size, width) 元组，width 为页面宽度减去 x 方向的 margin
        """
        page_sizes = {
            "A5": ("A5", "148mm"),
            "A4": ("A4", "210mm"),
            "A3": ("A3", "297mm"),
            "Letter": ("Letter", "8.5in"),
            "Legal": ("Legal", "8.5in"),
        }

        page_size, full_width = page_sizes.get(self.size, ("A4", "210mm"))
        usable_width = f"calc({full_width} - {self._get_x_margin_expression()})"

        return (page_size, usable_width)

    def get_header_html(self) -> str:
        if self.header:
            return self.header
        else:
            return f"""
            <div class="flex flex-row justify-between w-full">
                <div>{self.header_left}</div>
                <div>{self.header_center}</div>
                <div>{self.header_right}</div>
            </div>
            """

    def get_footer_html(self) -> str:
        if self.footer:
            return self.footer
        else:
            return f"""
            <div class="flex flex-row justify-between w-full">
                <div>{self.footer_left}</div>
                <div>{self.footer_center}</div>
                <div>{self.footer_right}</div>
            </div>
            """


class ContextOptions:
    def __init__(
        self,
        *,
        enable_debug: bool = False,
        enable_substitution: bool = True,
        suppress_private_assignments: bool = True,
        record_structured_steps: bool = True,
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
        self.doc_title: str = "UzonCalc Calculation Sheet"
        self.page_info: PageInfo = PageInfo()

        # 自定义样式字典，格式为 {选择器: {属性: 值}}
        # 例如: {"body": {"font_size": "14px", "line_height": "1.8"}}
        self.styles: dict[str, dict] = {}
