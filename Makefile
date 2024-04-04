.PHONY: lint format type-check sort-imports nice

lint:
	poetry run autopep8 .

format:
	poetry run black .

sort-imports:
	poetry run isort .

type-check:
	poetry run mypy .

nice: lint format sort-imports