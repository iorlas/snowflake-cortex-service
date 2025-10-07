import json
import os
from typing import Any, Iterator

import pandas as pd
import requests
import snowflake.connector
import sseclient
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DATABASE = os.getenv("SNOWFLAKE_DATABASE", "CORTEX_ANALYST_DEMO")
SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "REVENUE_TIMESERIES")
STAGE = os.getenv("SNOWFLAKE_STAGE", "RAW_DATA")
FILE = os.getenv("SNOWFLAKE_FILE", "revenue_timeseries.yaml")

app = FastAPI()

# Initialize Snowflake connection
conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
)


class QuestionRequest(BaseModel):
    question: str


class AnalystResponse(BaseModel):
    text: str
    sql_queries: list[str]
    results: list[list[dict[str, Any]]]


def send_message(question: str) -> requests.Response:
    """Calls the Cortex Analyst API."""
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
        "semantic_model_file": f"@{DATABASE}.{SCHEMA}.{STAGE}/{FILE}",
        "stream": True,
    }
    resp = requests.post(
        url=f"https://{conn.host}/api/v2/cortex/analyst/message",
        json=request_body,
        headers={
            "Authorization": f'Snowflake Token="{conn.rest.token}"',
            "Content-Type": "application/json",
        },
        stream=True,
    )
    if resp.status_code < 400:
        return resp
    else:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Failed request: {resp.text}",
        )


def process_stream(events: Iterator[sseclient.Event]) -> tuple[str, list[str]]:
    """Process the streaming response and extract text and SQL queries."""
    text_parts = []
    sql_queries = []
    current_sql = []
    in_sql_block = False

    while True:
        event = next(events, None)
        if not event:
            break

        data = json.loads(event.data)

        match event.event:
            case "message.content.delta":
                match data["type"]:
                    case "sql":
                        if not in_sql_block:
                            in_sql_block = True
                            current_sql = []
                        current_sql.append(data["statement_delta"])
                    case "text":
                        if in_sql_block:
                            sql_queries.append("".join(current_sql))
                            in_sql_block = False
                        text_parts.append(data["text_delta"])
                    case "suggestions":
                        text_parts.append(data["suggestions_delta"]["suggestion_delta"])
            case "status":
                if data["status_message"].lower() == "done":
                    if in_sql_block:
                        sql_queries.append("".join(current_sql))
                    break
            case "error":
                raise HTTPException(status_code=500, detail=data)

    return "".join(text_parts), sql_queries


@app.post("/ask", response_model=AnalystResponse)
async def ask_question(request: QuestionRequest):
    """Process a question through Cortex Analyst and return results."""
    try:
        response = send_message(request.question)
        events = sseclient.SSEClient(response.iter_content()).events()

        text, sql_queries = process_stream(events)

        # Execute SQL queries and collect results
        results = []
        for sql_query in sql_queries:
            df = pd.read_sql(sql_query, conn)
            results.append(df.to_dict(orient="records"))

        return AnalystResponse(
            text=text,
            sql_queries=sql_queries,
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
