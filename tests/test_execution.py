# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name
import pytest


def test_pass(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="```python\nprint('test-output', end='')\n```")
    result = pytester.runpytest("--docfiles", "-s")
    result.stdout.re_match_lines([r"doc\.md test-output\."])


def test_rewrite_assertion(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="```python\nassert 'A' == 'B', 'message'\n```")
    result = pytester.runpytest("--docfiles")
    result.stdout.fnmatch_lines(
        [
            "E   AssertionError: message",
            "E   assert 'A' == 'B'",
            "E     - B",
            "E     + A",
        ]
    )


def test_rewrite_stacktrace(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(module="def fn():\n    raise Exception('e')\n")
    pytester.syspathinsert(".")
    pytester.makefile(
        ".md", doc="# heading\n```python\nimport module\nmodule.fn()\n```"
    )
    result = pytester.runpytest("--docfiles", "--tb=short", "-k", "doc.md")
    result.stdout.fnmatch_lines(
        [
            "_* test session _*",
            "doc.md:4: in section <python-section-0>",
            "    module.fn()",
            "module.py:2: in fn",
            "    raise Exception('e')",
            "E   Exception: e",
        ]
    )
