from dataclasses import dataclass, field
from typing import Callable

from sqlglot import exp

from guardrails.parser import ParsedQuery, extract_dml_type, has_dangerous_function
from guardrails.exceptions import GuardrailsError, SecurityError, SyntaxError_, ComplexityError


@dataclass
class RuleResult:
    passed: bool
    rule_id: str
    message: str
    error: GuardrailsError | None = None
    action: str = "block"


@dataclass
class Rule:
    rule_id: str
    description: str
    check_fn: Callable[[ParsedQuery], RuleResult]
    action: str = "block"  # "block" or "warn"


DANGEROUS_FUNCTIONS = {"load_extension", "sqlite_version", "exec", "eval"}
DANGEROUS_STATEMENTS = {"INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"}
TRANSACTION_CONTROL = {"BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT"}


def check_ddl_dml(parsed: ParsedQuery) -> RuleResult:
    for stmt in parsed.statements:
        if stmt is None:
            continue
        dtype = extract_dml_type(stmt)
        if dtype in DANGEROUS_STATEMENTS:
            return RuleResult(passed=False, rule_id="G001",
                              message=f"Blocked {dtype} statement - only SELECT allowed",
                              error=SecurityError(f"Destructive statement blocked: {dtype}"), action="block")
    return RuleResult(passed=True, rule_id="G001", message="No dangerous statements found")



def check_transaction_control(parsed: ParsedQuery) -> RuleResult:
    sql_upper = parsed.original_sql.strip().upper()
    for kw in TRANSACTION_CONTROL:
        if sql_upper.startswith(kw):
            return RuleResult(passed=False, rule_id="G002",
                              message=f"Blocked transaction control: {kw}",
                              error=SecurityError(f"Transaction control blocked: {kw}"), action="block")
    return RuleResult(passed=True, rule_id="G002", message="No transaction control")


def check_comments(parsed: ParsedQuery) -> RuleResult:
    if parsed.has_comment:
        return RuleResult(passed=False, rule_id="G003",
                          message="SQL comments are not allowed",
                          error=SecurityError("Comments detected in SQL"), action="block")
    return RuleResult(passed=True, rule_id="G003", message="No comments")


def check_single_statement(parsed: ParsedQuery) -> RuleResult:
    if parsed.statement_count > 1:
        return RuleResult(passed=False, rule_id="G004",
                          message=f"Multiple statements detected ({parsed.statement_count})",
                          error=SecurityError("Multiple statements not allowed"), action="block")
    return RuleResult(passed=True, rule_id="G004", message="Single statement")


def check_limit(parsed: ParsedQuery, max_limit: int = 1000) -> RuleResult:
    for stmt in parsed.statements:
        if stmt is None:
            continue
        limit_node = stmt.find(exp.Limit)
        if limit_node is None and isinstance(stmt, exp.Select):
            return RuleResult(passed=False, rule_id="G006",
                              message="Missing LIMIT clause",
                              error=SecurityError("LIMIT clause required"), action="warn")
        elif limit_node and isinstance(stmt, exp.Select):
            try:
                val = int(limit_node.expression.name)
                if val > max_limit:
                    return RuleResult(passed=False, rule_id="G006",
                                      message=f"LIMIT {val} exceeds max of {max_limit}",
                                      error=SecurityError(f"LIMIT {val} > {max_limit}"), action="warn")
            except (ValueError, AttributeError):
                pass
    return RuleResult(passed=True, rule_id="G006", message="LIMIT valid")


def check_dangerous_functions(parsed: ParsedQuery) -> RuleResult:
    for stmt in parsed.statements:
        if stmt is None:
            continue
        if has_dangerous_function(stmt, DANGEROUS_FUNCTIONS):
            return RuleResult(passed=False, rule_id="G005",
                              message="Dangerous SQL function detected",
                              error=SecurityError("Dangerous function in SQL"), action="block")
    return RuleResult(passed=True, rule_id="G005", message="No dangerous functions")


def check_nesting_depth(parsed: ParsedQuery, max_depth: int = 5) -> RuleResult:
    if parsed.nesting_depth > max_depth:
        return RuleResult(passed=False, rule_id="G007",
                          message=f"Nesting depth {parsed.nesting_depth} exceeds limit {max_depth}",
                          error=ComplexityError("Query too deeply nested"), action="warn")
    return RuleResult(passed=True, rule_id="G007", message="Nesting depth OK")


def check_join_tables(parsed: ParsedQuery, max_tables: int = 8) -> RuleResult:
    if len(parsed.tables) > max_tables:
        return RuleResult(passed=False, rule_id="G008",
                          message=f"Query references {len(parsed.tables)} tables (max {max_tables})",
                          error=ComplexityError("Too many tables in query"), action="warn")
    return RuleResult(passed=True, rule_id="G008", message="Table count OK")


DEFAULT_RULES: list[Rule] = [
    Rule(rule_id="G001", description="Block DDL/DML operations", check_fn=check_ddl_dml, action="block"),
    Rule(rule_id="G002", description="Block transaction control", check_fn=check_transaction_control, action="block"),
    Rule(rule_id="G003", description="Block SQL comments", check_fn=check_comments, action="block"),
    Rule(rule_id="G004", description="Require single statement", check_fn=check_single_statement, action="block"),
    Rule(rule_id="G005", description="Block dangerous functions", check_fn=check_dangerous_functions, action="block"),
    Rule(rule_id="G006", description="Require LIMIT clause", check_fn=check_limit, action="warn"),
    Rule(rule_id="G007", description="Check nesting depth", check_fn=check_nesting_depth, action="warn"),
    Rule(rule_id="G008", description="Check table count", check_fn=check_join_tables, action="warn"),
]