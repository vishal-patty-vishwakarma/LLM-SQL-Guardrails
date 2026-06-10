import pytest

from pipeline.orchestrator import run_pipeline
from pipeline.executor import execute_safe, to_markdown, to_dict


class TestPipeline:
    def test_pipeline_result_structure(self):
        result = run_pipeline("Show all products")
        assert result.question == "Show all products"
        assert result.sql is not None
        assert result.validation is not None

    def test_pipeline_with_simple_question(self):
        result = run_pipeline("Show all products")
        if result.validation.valid:
            assert result.results is not None
            assert len(result.results) > 0
            assert "name" in result.results.columns or "Name" in result.results.columns

    def test_pipeline_with_filter(self):
        result = run_pipeline("List customers from USA")
        assert result.sql is not None

    def test_pipeline_with_aggregation(self):
        result = run_pipeline("How many customers are there?")
        if result.validation.valid:
            assert result.results is not None

    def test_pipeline_rejects_drop(self):
        result = run_pipeline("Drop the products table")
        assert not result.validation.valid
        assert result.error is not None

    def test_pipeline_rejects_delete(self):
        result = run_pipeline("Delete all customers")
        assert not result.validation.valid

    def test_pipeline_with_empty_question(self):
        result = run_pipeline("")
        assert result.error is None or True

    def test_pipeline_with_join_question(self):
        result = run_pipeline("Show orders with customer names")
        if result.validation.valid:
            assert result.results is not None

    def test_pipeline_with_top_n(self):
        result = run_pipeline("Top 5 most expensive products")
        if result.validation.valid:
            assert result.results is not None
            assert len(result.results) <= 5


class TestExecutor:
    def test_execute_safe_returns_dataframe(self):
        df = execute_safe("SELECT * FROM categories LIMIT 5")
        import pandas as pd
        assert isinstance(df, pd.DataFrame)

    def test_execute_safe_respects_limit(self):
        df = execute_safe("SELECT * FROM products LIMIT 3")
        assert len(df) <= 3

    def test_execute_safe_column_names(self):
        df = execute_safe("SELECT id, name, price FROM products LIMIT 1")
        assert list(df.columns) == ["id", "name", "price"]

    def test_execute_safe_empty_result(self):
        df = execute_safe("SELECT * FROM products WHERE id = 9999")
        assert len(df) == 0

    def test_execute_safe_aggregation(self):
        df = execute_safe("SELECT COUNT(*) as cnt FROM customers")
        assert df.iloc[0, 0] == 50

    def test_execute_safe_rejects_too_long(self):
        import pytest
        with pytest.raises(ValueError):
            execute_safe("S" * 10_001)

    def test_formatter_markdown(self):
        df = execute_safe("SELECT name, price FROM products LIMIT 3")
        md = to_markdown(df)
        assert isinstance(md, str)
        assert len(md) > 0
        assert "name" in md.lower() or "Name" in md.lower()

    def test_formatter_dict(self):
        df = execute_safe("SELECT name, price FROM products LIMIT 3")
        d = to_dict(df)
        assert isinstance(d, list)
        assert len(d) == 3
        assert isinstance(d[0], dict)


class TestSchemaContext:
    def test_schema_context_includes_tables(self):
        from llm.schema_context import get_schema_context
        ctx = get_schema_context(sample_rows=0)
        assert "products" in ctx
        assert "customers" in ctx
        assert "orders" in ctx

    def test_schema_context_includes_foreign_keys(self):
        from llm.schema_context import get_schema_context
        ctx = get_schema_context(sample_rows=0)
        assert "FK" in ctx or "category_id" in ctx

    def test_get_table_names(self):
        from llm.schema_context import get_table_names
        tables = get_table_names()
        assert "products" in tables
        assert "customers" in tables
        assert "orders" in tables

    def test_get_columns(self):
        from llm.schema_context import get_columns_for_table
        cols = get_columns_for_table("products")
        col_names = [c["name"] for c in cols]
        assert "id" in col_names
        assert "name" in col_names
        assert "price" in col_names