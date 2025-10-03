.PHONY: dev test docs sample lint

dev:
uv venv || true
uv pip install -e .[dev]
pre-commit install

lint:
ruff check .
mypy .

test:
pytest -q

docs:
mkdocs serve

sample:
python examples/quickstart.py
@echo "Artifacts in examples/out/"
