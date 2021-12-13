# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name
import pytest


def test_pass(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="```python\nprint('test-output', end='')\n```")
    result = pytester.runpytest("--docfiles", "-s")
    result.stdout.re_match_lines([r"doc\.md test-output\."])
