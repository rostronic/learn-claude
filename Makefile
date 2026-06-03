# Learn Claude — platform test suite (infrastructure, not coursework).
# `make install` once, then `make test` to validate the whole repo.
PY ?= python3

.PHONY: help install test test-structure test-infra

help:
	@echo "make install        install dev/test dependencies (requirements-dev.txt)"
	@echo "make test           run everything: structural validation + MCP server tests"
	@echo "make test-structure validate lessons, maps, questions, and starter syntax"
	@echo "make test-infra     run the grading + progress MCP server unit tests"

install:
	$(PY) -m pip install -r requirements-dev.txt

test: test-structure test-infra

test-structure:
	$(PY) -m pytest tests/ -q

test-infra:
	cd infra/grading-mcp && $(PY) -m pytest -q
	cd infra/progress-mcp && $(PY) -m pytest -q
