from dataclasses import dataclass
from uzoncalc import *


@dataclass(slots=True)
class RectangleSection:
    """矩形基础平面截面计算器。"""

    width: any # type: ignore
    height: any # type: ignore

    def outline_points(self) -> list[tuple[float, float]]:
        """返回用于绘图的闭合轮廓点。"""
        width_m = self.width.to(unit.meter).magnitude
        height_m = self.height.to(unit.meter).magnitude
        return [
            (0.0, 0.0),
            (width_m, 0.0),
            (width_m, height_m),
            (0.0, height_m),
            (0.0, 0.0),
        ]

    @property
    def area(self):
        return self.width * self.height

    @property
    def centroid_x(self):
        return self.width / 2

    @property
    def centroid_y(self):
        return self.height / 2

    @property
    def inertia_x(self):
        return self.width * self.height**3 / 12

    @property
    def inertia_y(self):
        return self.height * self.width**3 / 12

    @property
    def section_modulus_x(self):
        return self.inertia_x / (self.height / 2)

    @property
    def section_modulus_y(self):
        return self.inertia_y / (self.width / 2)

    @property
    def kern_x(self):
        return self.width / 6

    @property
    def kern_y(self):
        return self.height / 6


def build_rectangle_section(width, height) -> RectangleSection:
    """构造矩形截面，后续扩展其他截面时可复用该入口。"""
    return RectangleSection(width=width, height=height)


@uzon_calc()
async def sheet():
    width = 300 * unit.millimeter
    height = 500 * unit.millimeter
    section = build_rectangle_section(width=width, height=height)


if __name__ == "__main__":
    ctx = run_sync(sheet)
    ctx.save("../output/sub_function_caller.html")
