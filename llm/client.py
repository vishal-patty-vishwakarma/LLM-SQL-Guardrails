import logging
from typing import Generator

import ollama
from pydantic import BaseModel, Field

from config.settings import settings

logger = logging.getLogger(__name__)


class SQLGeneration(BaseModel):
    sql: str = Field(description="The generated SQL query")
    explanation: str | None = Field(default=None, description="Brief explanation of the SQL query")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Confidence score")


def generate_sql(prompt: str) -> SQLGeneration:
    response = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1, "num_predict": 512},
    )
    content = response["message"]["content"].strip()

    sql = _extract_sql(content)
    return SQLGeneration(sql=sql, explanation=None, confidence=None)


def generate_sql_stream(prompt: str) -> Generator[str, None, SQLGeneration]:
    stream = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1, "num_predict": 512},
        stream=True,
    )
    full_content = ""
    for chunk in stream:
        token = chunk["message"]["content"]
        full_content += token
        yield token

    sql = _extract_sql(full_content)
    yield SQLGeneration(sql=sql, explanation=None, confidence=None)


def _extract_sql(text: str, max_statements: int = 1) -> str:
    lines = text.split("\n")
    sql_lines = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith("```"):
            if "sql" in line.lower():
                in_code_block = True
            elif in_code_block:
                in_code_block = False
            continue
        if in_code_block:
            sql_lines.append(line)

    if sql_lines:
        raw = "\n".join(sql_lines).strip()
        return _take_first_statement(raw)

    for line in lines:
        stripped = line.strip().upper()
        if stripped.startswith("SELECT") or stripped.startswith("WITH"):
            start = lines.index(line)
            sql = "\n".join(lines[start:]).strip()
            end_keywords = ["\n\n", "\nQ:", "\nA:"]
            for ek in end_keywords:
                if ek in sql:
                    sql = sql.split(ek)[0]
            return _take_first_statement(sql.strip("; \n") + ";")

    return "SELECT 1 WHERE 1=0;"


def _take_first_statement(sql: str) -> str:
    parts = sql.split(";")
    for part in parts:
        stripped = part.strip()
        if stripped.upper().startswith("SELECT") or stripped.upper().startswith("WITH"):
            return stripped + ";"
    return parts[0].strip() + ";"