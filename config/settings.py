from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="phi", description="Ollama model name (phi=3.8B, sqlcoder:7b=7B)")
    ollama_timeout: int = Field(default=120, description="Request timeout in seconds")

    database_path: Path = Field(default=Path("data/text2sql.db"), description="SQLite database file path")
    database_echo: bool = Field(default=False, description="Echo SQL statements")

    guardrails_max_rows: int = Field(default=1000, description="Maximum rows to return")
    guardrails_max_cols: int = Field(default=50, description="Maximum columns to return")
    guardrails_query_timeout: int = Field(default=30, description="Query execution timeout in seconds")
    guardrails_require_limit: bool = Field(default=True, description="Require LIMIT clause")
    guardrails_max_limit: int = Field(default=1000, description="Maximum LIMIT value")
    guardrails_max_join_tables: int = Field(default=8, description="Maximum tables in JOIN")
    guardrails_max_nesting_depth: int = Field(default=5, description="Maximum CTE/subquery nesting depth")

    few_shot_count: int = Field(default=3, description="Number of few-shot examples in prompt")
    schema_sample_rows: int = Field(default=1, description="Sample rows per table in schema context")

    log_level: str = Field(default="INFO", description="Logging level")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


settings = Settings()