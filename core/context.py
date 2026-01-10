from typing import Any

from core.context_options import ContextOptions


class CalcContext:
    def __init__(self, *, name: str | None = None):
        self.name = name or "calc_ctx" + hex(id(self))

        self.options = ContextOptions()

        # 记录结果
        self.__contents = []

        # 记录行内内容的临时存储
        self.__inline_values: list[str] | None = None
        self.__inline_separator: str = " "

    @property
    def contents(self):
        return self.__contents

    # region content recording
    def append_content(self, content: str):
        if self.options.skip_content:
            return

        # 对 content 进行后处理
        for handler in self.options.post_handlers:
            content = handler.handle(content)

        # 若有 row_values，则添加到 row_values 中
        # 在其它地方将其转换成一行内容
        if self.__inline_values is not None:
            self.__inline_values.append(content)
            return

        self.__contents.append(content)

    def start_inline(self, separator: str = " "):
        self.__inline_separator = separator
        if self.__inline_values is not None:
            return

        self.__inline_values = []

    def end_inline(self):
        if self.__inline_values:
            combined = self.__inline_separator.join(self.__inline_values)
            # 将整行内容包装在 <p> 标签中
            self.__contents.append(f"<p>{combined}</p>")
            self.__inline_values = None

    @property
    def is_inline_mode(self) -> bool:
        """检查是否处于 inline 模式"""
        return self.__inline_values is not None

    # endregion

    # region result generation
    def html_content(self) -> str:
        return "\n".join(self.__contents)

    # endregion
