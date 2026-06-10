import pytest
from sqlalchemy import text

from guardrails.sql_validator import SQLValidator
from guardrails.parser import parse_sql, extract_dml_type
from sqlglot import exp


class TestParser:
    def test_parse_simple_select(self):
        parsed = parse_sql("SELECT * FROM products")
        assert parsed.is_valid
        assert "products" in parsed.tables
        assert parsed.statement_count == 1

    def test_parse_with_join(self):
        sql = "SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id"
        parsed = parse_sql(sql)
        assert parsed.is_valid
        assert "products" in parsed.tables
        assert "categories" in parsed.tables

    def test_parse_with_limit(self):
        parsed = parse_sql("SELECT * FROM products LIMIT 10")
        assert parsed.has_limit

    def test_parse_without_limit(self):
        parsed = parse_sql("SELECT * FROM products")
        assert not parsed.has_limit

    def test_parse_detects_comment(self):
        parsed = parse_sql("SELECT * FROM products -- comment")
        assert parsed.has_comment

    def test_parse_multi_statement(self):
        parsed = parse_sql("SELECT * FROM products; SELECT * FROM customers")
        assert parsed.statement_count == 2

    def test_parse_nested_subquery(self):
        sql = "SELECT * FROM products WHERE price > (SELECT AVG(price) FROM products)"
        parsed = parse_sql(sql)
        assert parsed.nesting_depth >= 1

    def test_extract_dml_select(self):
        parsed = list(exp.Select().find_all(exp.Select))
        stmt = exp.Select()
        assert extract_dml_type(stmt) == "SELECT"

    def test_extract_dml_drop(self):
        stmt = exp.Drop()
        assert extract_dml_type(stmt) == "DROP"

    def test_extract_dml_insert(self):
        stmt = exp.Insert()
        assert extract_dml_type(stmt) == "INSERT"


class TestValidator:
    def test_valid_sql_passes(self, validator):
        result = validator.validate("SELECT * FROM products LIMIT 10")
        assert result.valid
        assert len(result.errors) == 0

    def test_drop_blocked(self, validator):
        result = validator.validate("DROP TABLE orders")
        assert not result.valid
        assert any("DROP" in str(e) for e in result.errors)

    def test_delete_blocked(self, validator):
        result = validator.validate("DELETE FROM customers WHERE id = 1")
        assert not result.valid
        assert any("DELETE" in str(e) for e in result.errors)

    def test_insert_blocked(self, validator):
        result = validator.validate("INSERT INTO products (name, price) VALUES ('test', 10)")
        assert not result.valid

    def test_update_blocked(self, validator):
        result = validator.validate("UPDATE products SET price = 0")
        assert not result.valid

    def test_truncate_blocked(self, validator):
        result = validator.validate("TRUNCATE TABLE orders")
        assert not result.valid

    def test_comment_blocked(self, validator):
        result = validator.validate("SELECT * FROM users; -- comment")
        assert not result.valid

    def test_multi_statement_blocked(self, validator):
        result = validator.validate("SELECT * FROM customers; SELECT * FROM orders")
        assert not result.valid

    def test_transaction_blocked(self, validator):
        result = validator.validate("BEGIN TRANSACTION")
        assert not result.valid

    def test_dangerous_function_blocked(self, validator):
        result = validator.validate("SELECT load_extension('foo')")
        assert not result.valid

    def test_limit_warning(self, validator):
        result = validator.validate("SELECT * FROM products")
        assert result.valid
        assert len(result.warnings) > 0

    def test_valid_join_passes(self, validator):
        sql = "SELECT p.name, c.name FROM products p JOIN categories c ON p.category_id = c.id LIMIT 5"
        result = validator.validate(sql)
        assert result.valid

    def test_valid_subquery_passes(self, validator):
        sql = "SELECT name FROM products WHERE price > (SELECT AVG(price) FROM products) LIMIT 5"
        result = validator.validate(sql)
        assert result.valid

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM products LIMIT 10",
            "SELECT COUNT(*) FROM customers",
            "SELECT DISTINCT country FROM customers",
            "SELECT * FROM orders ORDER BY order_date DESC LIMIT 5",
            "SELECT p.name, SUM(oi.quantity) as total FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name LIMIT 10",
        ],
    )
    def test_all_valid_sql_passes(self, validator, sql):
        result = validator.validate(sql)
        assert result.valid, f"Expected valid: {sql}"

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE orders",
            "DELETE FROM customers",
            "INSERT INTO products VALUES (1, 'x')",
            "UPDATE products SET name = 'x'",
            "ALTER TABLE products ADD COLUMN x text",
            "SELECT * FROM users; SELECT * FROM orders",
        ],
    )
    def test_all_malicious_blocked(self, validator, sql):
        result = validator.validate(sql)
        assert not result.valid, f"Expected blocked: {sql}"

    def test_malicious_dataset_all_blocked(self, validator, malicious_queries):
        failures = []
        for item in malicious_queries:
            result = validator.validate(item["sql"])
            if item["expected_block"] and result.valid:
                failures.append(f"{item['id']}: {item['sql']} should have been blocked")
            if not item["expected_block"] and not result.valid:
                failures.append(f"{item['id']}: {item['sql']} should NOT have been blocked")
        assert not failures, "\n".join(failures)


class TestExecutor:
    def test_execute_valid_sql(self, db_engine):
        from pipeline.executor import execute_safe
        df = execute_safe("SELECT COUNT(*) as cnt FROM products")
        assert df is not None
        assert df.iloc[0, 0] == 15

    def test_execute_with_limit(self, db_engine):
        from pipeline.executor import execute_safe
        df = execute_safe("SELECT * FROM products LIMIT 5")
        assert len(df) <= 5

    def test_execute_join(self, db_engine):
        from pipeline.executor import execute_safe
        df = execute_safe("SELECT p.name, c.name as cat FROM products p JOIN categories c ON p.category_id = c.id LIMIT 10")
        assert len(df) > 0
        assert "cat" in df.columns