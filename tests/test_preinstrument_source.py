"""Tests for managed pure-source pre-instrumentation."""

from uzoncalc.handcalc.preinstrument import preinstrument_source


def test_preinstrumented_decorator_skips_runtime_ast_rebuild(monkeypatch) -> None:
    """Generated decorated functions should not call runtime instrument_function."""
    source = """
from uzoncalc import uzon_calc

@uzon_calc()
async def sheet():
    x = 1 + 2
    return x
"""
    result = preinstrument_source(
        source,
        filename="src/main.py",
        scope_key="scope_abc",
        dependency_defaults={},
    )

    import uzoncalc.startup as startup

    seen_marker = False

    def assert_preinstrumented(function):
        """Assert the decorator receives a marked function and return it unchanged."""
        nonlocal seen_marker
        seen_marker = getattr(function, "__uzon_instrumented__", False)
        return function

    monkeypatch.setattr(startup, "instrument_function", assert_preinstrumented)
    namespace: dict = {}
    exec(compile(result.source, "src/main.py", "exec"), namespace)

    assert getattr(namespace["sheet"], "_uzon_calc_entry") is True
    assert seen_marker is True
    assert result.instrumented_functions == ["sheet"]
    assert result.source_map[0]["originalStart"] == 5


def test_preinstrument_rewrites_default_and_explicit_calcdeps_imports() -> None:
    """Static dependency imports should resolve into artifact-local scopes."""
    source = """
from uzoncalc import uzon_calc
from calcdeps.beam.api import capacity
from calcdeps.beam.v_1_0_0.api import old_capacity

@uzon_calc()
async def sheet():
    value = capacity()
"""
    result = preinstrument_source(
        source,
        filename="src/main.py",
        scope_key="scope_deadbeef",
        dependency_defaults={"beam": "latest"},
    )

    assert "__uzon_deps__.scope_deadbeef.beam.latest.api" in result.source
    assert "__uzon_deps__.scope_deadbeef.beam.v_1_0_0.api" in result.source
