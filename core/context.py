from typing import Any

from core.context_options import ContextOptions
from core.renders.step_renderers import StepEvent


class CalcContext:
    def __init__(self, *, name: str | None = None):
        self.name = name or "calc_ctx" + hex(id(self))

        self.options = ContextOptions()

        # Aliases for symbols (used by core.renders.options.alias).
        self.aliases: dict[str, str] = {}

        # 记录结果
        self.__contents = []

        # 结构化记录步骤（可选），可用于调试输出
        self.__steps = []

    @property
    def contents(self):
        return self.__contents

    @property
    def steps(self):
        return self.__steps

    def append_content(self, content: str):
        if not self.options.skip_content:
            self.__contents.append(content)
