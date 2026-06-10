import logging
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from database.connection import engine
from config.settings import settings

logger = logging.getLogger(__name__)


def execute_safe(sql: str) -> pd.DataFrame:
    if len(sql) > 10_000:
        raise ValueError("Query exceeds maximum length of 10,000 characters")

    with engine.connect() as conn:
        conn.execute(text("PRAGMA query_only = ON"))
        conn.execute(text("PRAGMA temp_store = MEMORY"))

        result = conn.execute(text(sql))
        rows = result.fetchmany(settings.guardrails_max_rows + 1)
        cols = list(result.keys())

        if len(rows) > settings.guardrails_max_rows:
            rows = rows[:settings.guardrails_max_rows]

        if len(cols) > settings.guardrails_max_cols:
            cols = cols[:settings.guardrails_max_cols]
            rows = [row[:settings.guardrails_max_cols] for row in rows]

    df = pd.DataFrame(rows, columns=cols)
    return df


def to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "No results returned."
    return df.to_string(index=False)


def to_dict(df: pd.DataFrame) -> list[dict[str, Any]]:
    return df.to_dict(orient="records")