import ast

from core.context import CalcContext
from core.handcalc.field_names import FieldNames
from core.handcalc.ast_visitor import AstNodeVisitor
from core.handcalc.recorder import record_step


def test_expr_name_stmt_records_as_name_equals_value():
    run_module = ast.parse("b = 2\nb\n'hi'\nf\"x={b}\"\n")
    run_module = AstNodeVisitor().visit(run_module)
    ast.fix_missing_locations(run_module)

    ctx = CalcContext(name="test")
    env = {
        FieldNames.uzon_record_step: record_step,
        FieldNames.ctx: ctx,
    }

    exec(compile(run_module, filename="<ast>", mode="exec"), env, env)

    # 1) assignment line recorded (no nested <math>)
    assert ctx.contents[0].count("<math") == 1
    assert "<mi>b</mi>" in ctx.contents[0]

    # 2) bare name expression recorded as name=value (no nested <math>)
    assert ctx.contents[1].count("<math") == 1
    assert "<mi>b</mi>" in ctx.contents[1]

    # 3) pure string expression is output
    assert ctx.contents[2] == "<p>hi</p>"

    # 4) f-string expression is output (via value channel)
    assert ctx.contents[3] == "<p>x=2</p>"
