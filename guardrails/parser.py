from dataclasses import dataclass, field
from typing import Any

import sqlglot
from sqlglot import exp


@dataclass
class ParsedQuery:
    original_sql: str
    statements: list[exp.Expression] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    has_limit: bool = False
    has_comment: bool = False
    nesting_depth: int = 0
    statement_count: int = 0
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)


def parse_sql(sql: str) -> ParsedQuery:
    result = ParsedQuery(original_sql=sql)
    result.has_comment = "--" in sql or "/*" in sql

    try:
        parsed = list(sqlglot.parse(sql, read="sqlite"))
    except Exception as e:
        result.is_valid = False
        result.errors.append(str(e))
        return result

    valid_statements = [s for s in parsed if s is not None]
    failed_count = parsed.count(None)

    if failed_count > 0:
        result.is_valid = False
        result.errors.append(f"Could not parse {failed_count} statement(s). SQL may be incomplete or malformed.")
        return result

    result.statement_count = len(valid_statements)
    result.statements = valid_statements

    for statement in valid_statements:
        _extract_tables(statement, result)
        _extract_limit(statement, result)
        _extract_nesting(statement, result)

    return result


def _extract_tables(node: exp.Expression, result: ParsedQuery) -> None:
    for table in node.find_all(exp.Table):
        name = table.name
        if name and name not in result.tables:
            result.tables.append(name)


def _extract_limit(node: exp.Expression, result: ParsedQuery) -> None:
    if node.find(exp.Limit):
        result.has_limit = True


def _extract_nesting(node: exp.Expression, result: ParsedQuery) -> None:
    depth = 0
    for parent in node.walk():
        if isinstance(parent, (exp.Subquery, exp.With)):
            depth += 1
    result.nesting_depth = max(result.nesting_depth, depth)


def extract_dml_type(node: exp.Expression) -> str | None:
    if isinstance(node, exp.Select):
        return "SELECT"
    if isinstance(node, exp.Insert):
        return "INSERT"
    if isinstance(node, exp.Update):
        return "UPDATE"
    if isinstance(node, exp.Delete):
        return "DELETE"
    if isinstance(node, exp.Create):
        return "CREATE"
    if isinstance(node, exp.Drop):
        return "DROP"
    if isinstance(node, exp.Alter):
        return "ALTER"
    if isinstance(node, exp.Semicolon):
        return extract_dml_type(node.this)
    if isinstance(node, exp.Transaction):
        return "TRANSACTION"
    _CLASS_TO_DML = {"TruncateTable": "TRUNCATE", "Grant": "GRANT", "Revoke": "REVOKE"}
    for class_name, dml_name in _CLASS_TO_DML.items():
        cls = getattr(exp, class_name, None)
        if cls is not None and isinstance(node, cls):
            return dml_name
    return None


def has_dangerous_function(node: exp.Expression, dangerous: set[str]) -> bool:
    for func in node.find_all(exp.Func):
        if func.name.lower() in dangerous:
            return True
    return False