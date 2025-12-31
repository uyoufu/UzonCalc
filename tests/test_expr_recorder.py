import ast

from core.context import CalcContext
from core.handcalc.field_names import FieldNames
from core.handcalc.record_step import record_step
from core.handcalc.recorders.expr_recorder import ExprRecorder


def test_expr_name_stmt_records_as_name_equals_value():
    module = ast.parse("b")
    expr_stmt = module.body[0]
    assert isinstance(expr_stmt, ast.Expr)

    recorder = ExprRecorder()
    recorded = recorder.record(expr_stmt)
    assert isinstance(recorded, list)
    assert len(recorded) == 2

    # Build a runnable module that defines b and then runs the recorded statements.
    run_module = ast.Module(
        body=[
            ast.Assign(
                targets=[ast.Name(id="b", ctx=ast.Store())],
                value=ast.Constant(value=2),
            ),
            *recorded,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(run_module)

    ctx = CalcContext(name="test")
    env = {
        FieldNames.uzon_record_step: record_step,
        FieldNames.ctx: ctx,
    }

    exec(compile(run_module, filename="<ast>", mode="exec"), env, env)

    assert ctx.contents[-1] == "b = 2"
