import logging
import re
from dataclasses import dataclass

import pandas as pd
import sqlglot

from llm.client import generate_sql, SQLGeneration
from llm.prompts import build_prompt
from llm.schema_context import get_schema_context
from guardrails.sql_validator import validator, ValidationResult
from guardrails.exceptions import GuardrailsError
from pipeline.executor import execute_safe, to_markdown

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    question: str
    sql: str
    validation: ValidationResult
    results: pd.DataFrame | None = None
    markdown: str | None = None
    error: str | None = None
    generation: SQLGeneration | None = None


def _repair_sql(sql: str, question: str = "") -> str:
    numbers = re.findall(r"\b(\d+)\b", question)
    default_val = numbers[0] if numbers else "1"

    repaired = sql
    repaired = re.sub(r"HAVING\s+(\w+\([^)]*\))\s*(>|<|>=|<=|=|!=)\s*;", rf"HAVING \1 \2 {default_val};", repaired)
    repaired = re.sub(r"HAVING\s+(\w+\([^)]*\))\s*(>|<|>=|<=|=|!=)\s*$", rf"HAVING \1 \2 {default_val}", repaired)

    try:
        parsed = list(sqlglot.parse(repaired, read="sqlite"))
        if parsed and parsed[0] is not None:
            return repaired
    except Exception:
        pass
    return sql


def run_pipeline(question: str) -> PipelineResult:
    result = PipelineResult(question=question, sql="", validation=ValidationResult(valid=False, sql=""))

    try:
        schema = get_schema_context()
        prompt = build_prompt(question, schema)
        generation = generate_sql(prompt)
        result.generation = generation
        result.sql = generation.sql

        result.sql = _repair_sql(result.sql, question)

        validation = validator.validate(result.sql)
        result.validation = validation

        if not validation.valid:
            result.error = "; ".join(str(e) for e in validation.errors)
            return result

        df = execute_safe(result.sql)
        result.results = df
        result.markdown = to_markdown(df)

    except GuardrailsError as e:
        result.error = str(e)
    except Exception as e:
        result.error = f"Pipeline error: {e}"
        logger.exception("Pipeline failed")

    return result