"""pytest plugin to run code section in documentation files."""
import ast
import types
from pathlib import Path
from typing import Generator, Optional

import markdown_it
import py
import pytest
from _pytest.assertion.rewrite import rewrite_asserts
from _pytest.config.argparsing import Parser


class PythonCodeSection(pytest.Item):
    """pytest representation of a markdown python code section."""

    def __init__(self, name: str, parent: pytest.Collector, source: str, lineno: int):
        super().__init__(name, parent)
        self.lineno = lineno
        self.source = source

    def runtest(self) -> None:
        tree = ast.parse(self.source)

        rewrite_asserts(
            tree, self.source.encode("utf-8"), str(self.fspath), self.config
        )

        compiled = compile(tree, str(self.fspath), "exec", dont_inherit=True)
        mod = types.ModuleType(self.name)
        exec(compiled, mod.__dict__)  # pylint: disable=exec-used


def _code_tokens(
    path: Path, lang: str
) -> Generator[markdown_it.token.Token, None, None]:
    markdown = markdown_it.MarkdownIt()
    for token in markdown.parse(path.read_text(encoding="utf-8")):
        if token.tag == "code" and token.info == lang:
            yield token


class MarkdownFile(pytest.File):
    """pytest markdown file representation."""

    def collect(self) -> Generator[pytest.Item, None, None]:
        """Collects python code sections from a markdown file."""
        for num, token in enumerate(
            _code_tokens(Path(str(self.fspath)), lang="python")
        ):
            lineno = token.map[0] + 1  # type: ignore
            yield PythonCodeSection.from_parent(
                self,
                name=f"python-section-{num}",
                source=token.content,
                lineno=lineno,
            )


def pytest_addoption(parser: Parser) -> None:
    """Adds a docfiles option to pytest"""
    parser.addoption("--docfiles", action="store_true", default=False)


def pytest_collect_file(
    parent: pytest.Collector, path: py.path.local
) -> Optional[pytest.Collector]:
    """Collects all markdown files."""
    if parent.config.getoption("--docfiles"):
        if path.ext in ".md":
            return MarkdownFile.from_parent(parent, fspath=path)  # type: ignore
    return None
