# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands

- Run tests: `uv run pytest -p pytest_mock -v` or `make test`
- Run all checks: `make check` (runs ruff check, ruff format, ty check)
- Single test: `pytest tests/path/to/test_file.py::test_function_name`

## Project Architecture

This is a Snowflake Cortex Analyst wrapper with two interfaces:

### FastAPI Backend ([api.py](src/api.py))
- REST API exposing `/ask` endpoint for natural language queries
- Processes questions through Snowflake Cortex Analyst API
- Executes generated SQL queries and returns results as JSON
- Uses streaming response from Cortex Analyst to extract SQL and text

### Streamlit Frontend ([web.py](src/web.py))
- Interactive chat interface for Cortex Analyst
- Displays conversation history with SQL queries and visualizations
- Renders results as tables, line charts, and bar charts
- Maintains session state for conversation flow

### Snowflake Integration
Both interfaces connect to Snowflake using:
- Database: `CORTEX_ANALYST_DEMO`
- Schema: `REVENUE_TIMESERIES`
- Semantic model: `revenue_timeseries.yaml` from `RAW_DATA` stage
- Cortex Analyst API at `/api/v2/cortex/analyst/message`

## Running the Application

- FastAPI server: `uvicorn src.api:app --reload` (default port 8000)
- Streamlit app: `streamlit run src/web.py`
- Example API request: See [examples/demo.http](examples/demo.http)

## Code Standards

- Python 3.12+ with full type annotations
- Dependencies: FastAPI, Streamlit, Snowflake connector, pandas, requests, sseclient-py
- Always run `make check` before committing
