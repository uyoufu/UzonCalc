from dataclasses import dataclass


@dataclass
class FormattedAstNode:
    targets: str | None
    latex: str
    substitution: str

    # 起始是单位
    start_unit: bool = False
    # 末尾是单位
    end_unit: bool = False

    @property
    def full_unit(self) -> bool:
        return self.start_unit and self.end_unit
