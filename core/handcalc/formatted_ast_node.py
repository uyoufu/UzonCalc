from dataclasses import dataclass


@dataclass
class FormattedAstNode:
    targets: str | None
    expr: str
    substitution: str

    # 起始是单位
    start_unit: bool = False
    # 末尾是单位
    end_unit: bool = False
    # 是否包含变量
    contains_variable: bool = False

    @property
    def full_unit(self) -> bool:
        return self.start_unit and self.end_unit

    def clone(self) -> "FormattedAstNode":
        return FormattedAstNode(
            targets=self.targets,
            expr=self.expr,
            substitution=self.substitution,
            start_unit=self.start_unit,
            end_unit=self.end_unit,
            contains_variable=self.contains_variable,
        )
