import json
from pathlib import Path

import pytest

from database.connection import engine
from guardrails.sql_validator import SQLValidator
from guardrails.parser import parse_sql


@pytest.fixture
def validator():
    return SQLValidator()


@pytest.fixture
def malicious_queries():
    path = Path(__file__).parent / "test_data" / "malicious_queries.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def sample_questions():
    path = Path(__file__).parent / "test_data" / "sample_questions.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def db_engine():
    return engine