.PHONY: lint type-check sort-imports nice clean reset

lint:
	poetry run autopep8 --recursive . --in-place
	poetry run black .

sort-imports:
	poetry run isort .
	poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place cloud_guardian --exclude=__init__.py

type-check:
	poetry run mypy .

nice: lint sort-imports

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .coverage

reset: clean
	rm -rf .venv
