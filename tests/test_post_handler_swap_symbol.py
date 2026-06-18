from core.uzoncalc.handcalc.post_handlers.swap_symbol import SwapSymbol


def test_swap_symbol_converts_greek_word():
    """希腊字母英文名称应转换为对应数学符号。"""
    handler = SwapSymbol()

    assert handler.handle("alpha") == "α"


def test_swap_symbol_unescapes_backslash_and_skips_conversion():
    """反斜杠转义的希腊字母英文名称应保持英文名称。"""
    handler = SwapSymbol()

    assert handler.handle(r"\alpha") == "alpha"


def test_swap_symbol_no_longer_skips_quoted_text():
    """引号不再作为保护边界，引号内英文名称仍应转换。"""
    handler = SwapSymbol()

    assert handler.handle("'alpha' \"alpha\"") == "'α' \"α\""


def test_swap_symbol_converts_only_unescaped_greek_word():
    """转义和未转义的希腊字母英文名称混用时应分别处理。"""
    handler = SwapSymbol()

    assert handler.handle(r"\alpha (alpha)") == "alpha (α)"


def test_swap_symbol_does_not_convert_word_after_unconsumed_backslash():
    """无法作为独立转义标记消费的反斜杠后名称不应被二次匹配。"""
    handler = SwapSymbol()

    assert handler.handle(r"x\alpha") == r"x\alpha"
