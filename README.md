# pytest_docfiles
[![Build Status](https://github.com/stefanhoelzl/pytest_docfiles/workflows/push/badge.svg)](https://github.com/stefanhoelzl/pytest_docfiles/actions)
[![PyPI](https://img.shields.io/pypi/v/pytest_docfiles.svg)](https://pypi.org/project/pytest_docfiles/)
[![Downloads](https://img.shields.io/pypi/dm/pytest_docfiles?color=blue&logo=pypi&logoColor=yellow)](https://pypistats.org/packages/pytest_docfiles)
[![License](https://img.shields.io/pypi/l/pytest_docfiles.svg)](LICENSE)

pytest plugin to test code sections in your documentation.

## Installation
```bash
pip install pytest_docfiles
```

## Usage
Define code sections in your markdown files.
````md
<!-- doc.md -->
# Hello World
```python
print("hello world!")
```
````
run pytest on your markdown files with the `--docfiles` flag.
```bash
pytest --docfiles doc.md
```

## Features
### Section Names
Define names for your code sections so they can be better identified in your pytest output
````md
<!-- doc.md -->
```python {"name": "my-section"}
print("hello world")
```
````
```bash
$ pytest --docfiles doc.md
...
doc.md::my-section PASSED
...
```

### Fixtures
Define your fixtures in `conftest.py` as usual
```python
# conftest.py

import pytest

@pytest.fixture
def custom_fixture() -> str:
    return "fixture value"

@pytest.fixture(autouse=True)
def autouse() -> None:
    """autouse fixtures are used in each code section"""
```
use the fixtures in your code sections
````md
<!-- doc.md -->
```python {"fixtures": ["custom_fixture"]}
assert custom_fixture == "fixture value"
```
````

### Scopes
Code section depending on other code section can be executed in scopes.
````md
```python {"scope": "my-scope"}
value = True
```
```python {"scope": "my-scope"}
assert value is True
```
````

### Skip Sections
````md
```python {"skip": true}
raise Exception("this section should not run")
```
````

### Exception Handling
````md
```python {"raises": "RuntimeError"}
raise RuntimeError("this section should pass")
```
````