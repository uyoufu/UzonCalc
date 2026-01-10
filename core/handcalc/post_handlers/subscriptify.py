import re

from core.handcalc.post_handlers.base_post_handler import BasePostHandler


class Subscriptify(BasePostHandler):
    """后处理器：将形如 a_b 的变量名渲染为下标。

    仅处理 MathML 中的 <mi>name</mi> 形式：
    - a_b -> <msub><mi>a</mi><mi>b</mi></msub>
    - x_1 -> <msub><mi>x</mi><mn>1</mn></msub>
    - x_1_2 -> 嵌套 <msub>( (x_1)_2 )

    规则（尽量保守）：
    - 以 '_' 开头/结尾的不处理（如 _tmp / tmp_）
    - 含连续 '_' 的不处理（如 concrete__code）
    """

    _mi_pattern = re.compile(r"<mi>([^<]+)</mi>")

    def handle(self, data: str) -> str:
        if "<mi>" not in data or "_" not in data:
            return data

        def _repl(m: re.Match[str]) -> str:
            name = m.group(1)
            if "_" not in name:
                return m.group(0)
            if name.startswith("_") or name.endswith("_"):
                return m.group(0)

            parts = name.split("_")
            if len(parts) < 2:
                return m.group(0)
            if any(p == "" for p in parts):
                return m.group(0)

            base_xml = f"<mi>{parts[0]}</mi>"
            for sub in parts[1:]:
                sub_xml = f"<mtext>{sub}</mtext>"
                base_xml = f"<msub>{base_xml}{sub_xml}</msub>"

            return base_xml

        return self._mi_pattern.sub(_repl, data)
