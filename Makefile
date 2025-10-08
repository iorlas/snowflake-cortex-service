test:
	uv run pytest -p pytest_mock -v

check:
	uv run ruff format .
	uv run ruff check . --fix
	uv run ty check


run:
	uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
