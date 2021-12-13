# pylint: disable=missing-module-docstring,missing-function-docstring,redefined-outer-name
import py
import pytest
from _pytest.cacheprovider import Cache
from _pytest.config import Config

from pytest_docfiles.plugin import MarkdownFile


@pytest.fixture
def disabled(pytester: pytest.Pytester) -> Config:
    return pytester.parseconfig()


@pytest.fixture
def enabled(pytester: pytest.Pytester) -> Config:
    config = pytester.parseconfig("--docfiles")
    config.cache = Cache(cachedir=pytester.path, config=config)
    return config


def test_addoption(enabled: Config, disabled: Config) -> None:
    assert not disabled.option.docfiles
    assert enabled.option.docfiles


def test_collect_file_disabled(pytester: pytest.Pytester, disabled: Config) -> None:
    pytester.makefile(".md", doc="")
    with pytest.raises(pytest.UsageError):
        pytester.getnode(disabled, "doc.md")


def test_collect_file_enabled(pytester: pytest.Pytester, enabled: Config) -> None:
    pytester.makefile(".nonmd", doc="")
    pytester.makefile(".md", doc="")

    node = pytester.getnode(enabled, "doc.md")
    assert isinstance(node, MarkdownFile)
    assert node.fspath == py.path.local("doc.md")


def test_collect_file_wrong_file(pytester: pytest.Pytester, enabled: Config) -> None:
    pytester.makefile(".nonmd", doc="")
    with pytest.raises(pytest.UsageError):
        pytester.getnode(enabled, "doc.nonmd")
