"""Every exercise starter file must parse (syntax check).

We compile rather than import/run: starters ship with `raise NotImplementedError`
and their pytest suites only pass against a learner's correct implementation, so
running them green here is not the goal. Compiling catches syntax errors in both
the skeleton and the test files without needing the `anthropic` SDK installed.
"""

import pathlib
import py_compile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
STARTER_PY = sorted(REPO.glob("lessons/module-*/*/starter/**/*.py"))
IDS = [str(f.relative_to(REPO)) for f in STARTER_PY]


def test_starters_exist():
    assert STARTER_PY, "no starter .py files found"


@pytest.mark.parametrize("path", STARTER_PY, ids=IDS)
def test_starter_compiles(path):
    py_compile.compile(str(path), doraise=True)
