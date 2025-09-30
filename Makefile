.PHONY: install lint format type test qa docs

install:
	pip install -e .[dev]

lint:
	ruff check .

format:
	ruff format .

type:
	mypy src

test:
	pytest

qa: lint type test

docs:
	@echo "Documentation lives under docs/."
