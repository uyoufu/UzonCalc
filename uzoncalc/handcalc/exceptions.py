"""统一的异常定义和错误处理机制"""


class HandcalcError(Exception):
    """handcalc 模块的基础异常类"""
    pass


class InstrumentationError(HandcalcError):
    """AST 插桩过程中的错误"""
    pass


class AstConversionError(HandcalcError):
    """AST 转换过程中的错误"""
    pass


class ValidationError(HandcalcError):
    """AST 验证失败"""
    pass
