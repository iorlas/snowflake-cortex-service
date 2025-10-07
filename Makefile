test:
	uv run pytest -p pytest_mock -v

check:
# 	osascript -e 'display notification "CHECK IS RAN"'
	uv run ruff check . --fix
	uv run ruff format .
	uv run ty check


run:
	uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload