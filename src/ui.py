"""⚠️ 此模块已废弃，请使用 src.ui 包。

新用法:
    from src.ui import STYLES, render_sidebar, render_messages, render_solution_card
"""

from .ui.solution import _parse_sections as _ps  # noqa


def result_tabs(result: dict) -> None:
    """向前兼容 — 直接调用完整方案渲染"""
    from .ui.solution import _render_full_solution
    _render_full_solution(result.get("content", ""))
