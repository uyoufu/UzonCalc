from typing import Any

from core.context_options import ContextOptions
from core.renders.step_renderers import StepEvent


class CalcContext:
    def __init__(self, *, name: str | None = None):
        self.name = name or "calc_ctx" + hex(id(self))

        self.options = ContextOptions()

        # 记录结果
        self.__contents = []

        self.__inline_values: list[str] | None = None

    @property
    def contents(self):
        return self.__contents

    # region content recording
    def append_content(self, content: str):
        if self.options.skip_content:
            return

        # 若有 row_values，则添加到 row_values 中
        # 在其它地方将其转换成一行内容
        if self.__inline_values is not None:
            self.__inline_values.append(content)
            return

        self.__contents.append(content)

    def start_inline(self):
        if self.__inline_values is not None:
            return

        self.__inline_values = []

    def end_inline(self):
        if self.__inline_values:
            combined = " ".join(self.__inline_values)
            self.__contents.append(combined)
            self.__inline_values = None

    # endregion

    # region result generation
    def html_content(self) -> str:
        return "\n".join(self.__contents)

    # endregion
