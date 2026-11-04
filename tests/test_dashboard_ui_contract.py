"""Guard against recurring dashboard usability regressions."""
import ast
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_getting_started_guide_has_real_markdown_line_breaks():
    guide = APP.split('with st.expander("New here? Follow this 3-step setup"', 1)[1]
    guide = guide.split("# Navigation targets", 1)[0]
    assert r"\\\\n" not in guide
    assert r"\n\n" in guide
    for step in ("1. **", "2. **", "3. **"):
        assert step in guide


def test_streamlit_expanders_are_not_nested():
    tree = ast.parse(APP)

    def is_expander(node):
        return (
            isinstance(node, ast.With)
            and any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Attribute)
                and isinstance(item.context_expr.func.value, ast.Name)
                and item.context_expr.func.value.id == "st"
                and item.context_expr.func.attr == "expander"
                for item in node.items
            )
        )

    def check(node, inside_expander=False):
        if is_expander(node):
            assert not inside_expander, f"Nested Streamlit expander at line {node.lineno}"
            inside_expander = True
        for child in ast.iter_child_nodes(node):
            check(child, inside_expander)

    check(tree)


def test_daily_results_have_clear_metric_labels():
    for label in ("Household demand", "Solar production", "Generator production", "Energy shortfall"):
        assert f'.metric("{label}"' in APP
