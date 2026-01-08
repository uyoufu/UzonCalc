"""handcalc v2

This package provides a structured pipeline:
AST -> Math IR (dict-based) -> (optional passes) -> MathML rendering.

V2 intentionally centralizes MathML wrapping (<math>/<mrow>) in the renderer
so nested <math> cannot occur.
"""

from .record import record_step  # re-export
