from matplotlib import pyplot as plt
from pint import UnitRegistry

from core.html_template import get_html_template
from core.setup import uzon_calc
from core.utils.doc import doc_title, page_size, style
from core.utils.elements import row


@uzon_calc()
def sheet(*, unit: UnitRegistry):
    from core.utils.options import hide, show
    from core.utils.elements import h, p, h1, div, span, input, plot

    doc_title("Cantilever Cap Beam Calculation")
    page_size("A4")

    hide()

    def add_cover(title: str, calculator: str, checker: str):
        """
        输出为 html
        大小为 A4 纵向页面
        包含标题、计算人、审核人等信息
        """

        style("a4-page", {"width": "210mm", "height": "297mm", "margin": "20mm"})

        row(
            [
                h1(title, props={"style": "text-align: center;"}, prevent=True),
                row(
                    [
                        p(
                            "计算人: {}".format(calculator),
                            props={"style": "text-align: center;"},
                            prevent=True,
                        ),
                    ]
                ),
            ]
        )

        div(
            [
                h1(title, props={"style": "text-align: center;"}, prevent=True),
                p(
                    "计算人: {}".format(calculator),
                    props={"style": "text-align: center;"},
                    prevent=True,
                ),
                p(
                    "审核人: {}".format(checker),
                    props={"style": "text-align: center;"},
                    prevent=True,
                ),
            ],
            props={"class": "a4-page"},
        )

    show()

    add_cover(
        title="18m宽钢混组合梁下部结构计算书",
        calculator="张三",
        checker="李呈",
    )

    # 计算部分
    h1("概述")

    """跨八一七路、五一路高架桥第六联采用 (42+49.5+50+46)m 钢混组合连续梁，桥面宽度 18m，平面位于曲线上。
        桥面布置为：0.5（防撞护栏）+8.0（机动车道）+1.0（中央护栏）+8.0（机动车道）+0.5（防撞护栏），设双向 2.0％ 横坡。
        桥面铺装为 6cm 中粒式沥青混凝土+4cm细粒式沥青混凝土，铺装总厚度 10cm。边防撞护栏和中央防撞护栏均采用混凝土防撞护栏。 
        桥墩一般构造图如下。"""


if __name__ == "__main__":
    ctx = sheet()  # type: ignore
    html_content = get_html_template("\n".join(ctx.contents))
    # 保存为 HTML 文件
    with open("calculation_sheet.html", "w", encoding="utf-8") as f:
        f.write(html_content)
