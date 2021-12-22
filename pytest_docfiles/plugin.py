"""pytest plugin to run code section in documentation files."""
import ast
import itertools
import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

import markdown_it
import py
import pytest
from _pytest._code.code import ExceptionInfo, TerminalRepr, TracebackEntry
from _pytest.assertion.rewrite import rewrite_asserts
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureRequest
from _pytest.mark import Mark


class SectionTracebackEntry(TracebackEntry):
    """Proxy for TracebackEntries to adjust line numbers and name of code sections."""

    def __init__(
        self,
        parent: TracebackEntry,
        line_offset: int,
        section_name: str,
    ) -> None:
        super().__init__(rawentry=parent._rawentry, excinfo=parent._excinfo)
        self._repr_style = parent._repr_style

        self.line_offset = line_offset
        self.section_name = section_name

    @property
    def lineno(self) -> int:
        return super().lineno + self.line_offset

    @property
    def name(self) -> str:
        return f"section <{self.section_name}>"


class PythonCodeSection(pytest.Item):
    """pytest representation of a markdown python code section."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        parent: pytest.Collector,
        source: str,
        lineno: int,
        fixtures: List[str],
        scope: Dict[str, Any],
    ):
        super().__init__(name, parent)
        self.lineno = lineno
        self.source = source
        self.scope = scope
        self.own_markers = [Mark("usefixtures", args=tuple(fixtures), kwargs={})]

        self.funcargs = {}  # type: ignore
        self._fixtureinfo = None

    def _setup_fixture_request(self) -> FixtureRequest:
        fixturemanager = (
            self.session._fixturemanager  # pylint: disable=protected-access
        )
        self._fixtureinfo = fixturemanager.getfixtureinfo(  # type: ignore
            node=self, func=None, cls=None, funcargs=False
        )
        fixture_request = FixtureRequest(self, _ispytest=True)
        fixture_request._fillfixtures()  # pylint: disable=protected-access
        return fixture_request

    def runtest(self) -> None:
        tree = ast.parse(self.source)

        rewrite_asserts(
            tree, self.source.encode("utf-8"), str(self.fspath), self.config
        )

        compiled = compile(tree, str(self.fspath), "exec", dont_inherit=True)
        fixture_request = self._setup_fixture_request()
        for fixture in ["tmp_path"]:
            self.scope[fixture] = fixture_request.getfixturevalue(fixture)

        exec(compiled, self.scope)  # pylint: disable=exec-used

    def repr_failure(
        self,
        excinfo: ExceptionInfo[BaseException],
        style: Optional[Any] = None,
    ) -> Union[str, TerminalRepr]:
        def _is_doc_item(entry: TracebackEntry) -> bool:
            return Path(str(entry.path)).absolute() == Path(str(self.fspath)).absolute()

        def _wrap_doc_entry(entry: TracebackEntry) -> SectionTracebackEntry:
            return SectionTracebackEntry(entry, self.lineno, self.name)

        excinfo.traceback[:] = list(
            map(
                lambda e: _wrap_doc_entry(e) if _is_doc_item(e) else e,
                itertools.dropwhile(_is_doc_item, excinfo.traceback),
            )
        )
        return super().repr_failure(excinfo, style)


def _code_tokens(
    path: Path, lang: str
) -> Generator[markdown_it.token.Token, None, None]:
    markdown = markdown_it.MarkdownIt()
    for token in markdown.parse(path.read_text(encoding="utf-8")):
        if token.tag == "code" and token.info.startswith(lang):
            yield token


class MarkdownFile(pytest.File):
    """pytest markdown file representation."""

    def collect(self) -> Generator[pytest.Item, None, None]:
        """Collects python code sections from a markdown file."""
        lang = "python"
        scopes: Dict[str, Dict[str, Any]] = {}
        for num, token in enumerate(_code_tokens(Path(str(self.fspath)), lang=lang)):
            lineno = token.map[0] + 1  # type: ignore
            args = token.info[len(lang) :].strip()
            parsed_args = json.loads(args) if args else {}
            yield PythonCodeSection.from_parent(
                self,
                name=parsed_args.get("name", f"python-section-{num}"),
                source=token.content,
                lineno=lineno,
                fixtures=parsed_args.get("fixtures", []),
                scope=scopes.setdefault(parsed_args.get("scope"), {}),
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
