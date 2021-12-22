# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name
import pytest


def test_collect_nothing(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="# only header")
    items, _ = pytester.inline_genitems("--docfiles")
    assert not items


def test_collect_and_parse_code_section(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="first\nsecond\n```python\n# comment\npass\n```")

    items, _ = pytester.inline_genitems("--docfiles")

    assert len(items) == 1
    assert items[0].name == "python-section-0"
    assert items[0].lineno == 3  # type: ignore
    assert items[0].source == "# comment\npass\n"  # type: ignore


def test_parse_custom_name(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="""```python {"name": "name"}\n\n```""")

    items, _ = pytester.inline_genitems("--docfiles")

    assert items[0].name == "name"


def test_dont_collect_non_python_code_section(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="```non-python\n```")
    items, _ = pytester.inline_genitems("--docfiles")
    assert not items
