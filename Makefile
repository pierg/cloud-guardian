.PHONY: lint type-check sort-imports nice

lint:
	poetry run autopep8 --recursive . --in-place
	poetry run black .

sort-imports:
	poetry run isort .
	poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place cloud_guardian --exclude=__init__.py

type-check:
	poetry run mypy .

nice: lint sort-imports
