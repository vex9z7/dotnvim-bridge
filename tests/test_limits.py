from __future__ import annotations

from dotnvim_bridge.limits import limit_text_lines, split_lines, tail_lines


def test_tail_lines_returns_all_when_under_limit() -> None:
    lines, truncated = tail_lines(["a", "b"], 3)
    assert lines == ["a", "b"]
    assert truncated is False


def test_tail_lines_truncates_from_front() -> None:
    lines, truncated = tail_lines(["a", "b", "c"], 2)
    assert lines == ["b", "c"]
    assert truncated is True


def test_limit_text_lines_reports_counts() -> None:
    result = limit_text_lines(["a", "b", "c"], 2)
    assert result == {
        "lines": ["b", "c"],
        "line_count": 3,
        "returned_line_count": 2,
        "truncated": True,
    }


def test_split_lines_empty_output() -> None:
    assert split_lines("") == []
