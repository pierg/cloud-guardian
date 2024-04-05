.PHONY: lint type-check sort-imports nice

lint:
	poetry run autopep8 --recursive . --in-place
	poetry run black .

sort-imports:
	poetry run isort .

type-check:
	poetry run mypy .

nice: lint sort-imports
