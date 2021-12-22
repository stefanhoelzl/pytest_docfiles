# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name
import pytest


def joined(*lines: str) -> str:
    return "\n".join(lines)


def test_pass(pytester: pytest.Pytester) -> None:
    pytester.makefile(".md", doc="```python\nprint('test-output', end='')\n```")
    result = pytester.runpytest("--docfiles", "-s")
    result.stdout.re_match_lines([r"doc\.md test-output\."])


def test_rewrite_assertion(pytester: pytest.Pytester) -> None:
    pytester.makefile(
        ".md",
        doc=joined(
            "```python\nassert 'A' == 'B', 'message'",
            "```",
        ),
    )
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
    pytester.makepyfile(
        module=joined(
            "def fn():",
            "    raise Exception('e')",
        )
    )
    pytester.syspathinsert(".")
    pytester.makefile(
        ".md",
        doc=joined(
            "# heading",
            "```python",
            "import module",
            "module.fn()",
            "```",
        ),
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


def test_fixtures_autouse(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(
        joined(
            "import os, pytest",
            "@pytest.fixture(autouse=True)",
            "def set_test_env_variable():",
            "    os.environ['TEST_AUTOUSE_FIXTURE'] = '1'",
        )
    )
    pytester.makefile(
        ".md",
        doc=joined(
            "```python",
            "import os",
            "assert os.environ['TEST_AUTOUSE_FIXTURE'] == '1'",
            "```",
        ),
    )
    result = pytester.runpytest("--docfiles", "-k", "doc.md")
    assert result.ret == 0


def test_explicit_use_fixture(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(
        joined(
            "import os, pytest",
            "@pytest.fixture",
            "def set_test_env_variable():",
            "    os.environ['TEST_EXPLICIT_USE_FIXTURE'] = '1'",
        )
    )
    pytester.makefile(
        ".md",
        doc=joined(
            """```python {"fixtures": ["set_test_env_variable"]}""",
            "import os",
            "assert os.environ['TEST_EXPLICIT_USE_FIXTURE'] == '1'",
            "```",
        ),
    )
    result = pytester.runpytest("--docfiles", "-k", "doc.md")
    assert result.ret == 0


def test_inject_fixtures_into_global_namespace(pytester: pytest.Pytester) -> None:
    pytester.makefile(
        ".md",
        doc=joined(
            """```python {"fixtures": ["tmp_path"]}""",
            "assert tmp_path.exists()",
            "```",
        ),
    )
    result = pytester.runpytest("--docfiles", "-k", "doc.md")
    assert result.ret == 0


def test_scopes(pytester: pytest.Pytester) -> None:
    pytester.makefile(
        ".md",
        doc=joined(
            """```python {"scope": "scope"}""",
            "value = 1",
            "```",
            """```python {"scope": "scope"}""",
            "assert value == 1",
            "```",
        ),
    )
    result = pytester.runpytest("--docfiles", "-k", "doc.md")
    assert result.ret == 0


def test_skip(pytester: pytest.Pytester) -> None:
    pytester.makefile(
        ".md",
        doc=joined(
            """```python {"skip": true}""",
            "raise RuntimeError('should not run')",
            "```",
        ),
    )
    result = pytester.runpytest("--docfiles", "-k", "doc.md")
    assert result.ret == 0
