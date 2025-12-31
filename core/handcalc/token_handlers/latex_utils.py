import ast


def latex_literal(text: str) -> str:
    """Return a literal segment safe for passing through str.format.

    We must escape braces because record_step uses Python's str.format for
    substitution. In LaTeX, braces are common (subscripts, superscripts, \frac).
    """

    return text.replace("{", "{{").replace("}", "}}")


def latex_group(inner: str) -> str:
    """Wrap inner in literal braces, preserving any {placeholders} inside."""

    return "{{" + inner + "}}"


def wrap_parens(inner: str) -> str:
    return f"({inner})"


def precedence(node: ast.AST) -> int:
    """Higher number = binds tighter."""

    if isinstance(node, (ast.Call, ast.Attribute, ast.Subscript)):
        return 90

    if isinstance(node, ast.UnaryOp):
        return 75

    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Pow):
            return 80
        if isinstance(node.op, (ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.MatMult)):
            return 70
        if isinstance(node.op, (ast.Add, ast.Sub)):
            return 60
        return 50

    return 100


def needs_parens_in_binop(
    *, child: ast.AST, parent_op: ast.operator, side: str
) -> bool:
    """Whether a BinOp child needs parentheses under the given parent op.

    side: "left" | "right"
    """

    if not isinstance(child, ast.BinOp):
        return False

    child_prec = precedence(child)
    parent_prec = precedence(
        ast.BinOp(left=ast.Constant(0), op=parent_op, right=ast.Constant(0))
    )

    if child_prec < parent_prec:
        return True
    if child_prec > parent_prec:
        return False

    # Equal precedence: associativity / non-associativity.
    if isinstance(parent_op, ast.Pow):
        return side == "left"

    if side == "right":
        if isinstance(parent_op, ast.Add):
            return isinstance(child.op, ast.Sub)
        if isinstance(parent_op, ast.Sub):
            return isinstance(child.op, (ast.Add, ast.Sub))
        if isinstance(parent_op, ast.Mult):
            return isinstance(child.op, (ast.Div, ast.FloorDiv, ast.Mod, ast.MatMult))
        if isinstance(parent_op, (ast.Div, ast.FloorDiv, ast.Mod, ast.MatMult)):
            return isinstance(
                child.op, (ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.MatMult)
            )

    return False


def format_field_name_latex(name: str) -> str:
    """Format a python identifier as LaTeX, supporting underscore subscripts.

    Returned string is safe to pass through str.format.
    """

    parts = name.split("_")
    if len(parts) == 1:
        return latex_literal(name)

    main = latex_literal(parts[0])
    sub = latex_literal("".join(parts[1:]))
    return f"{main}_{latex_group(sub)}"
