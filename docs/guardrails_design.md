# Guardrails Design

## Why AST Parsing?

Regex-based SQL validation is fragile:
- `DROP TABLE users` - easy to catch
- `DROP/*comment*/TABLE users` - regex misses this
- `SELECT * FROM users; DROP TABLE orders; --` - needs semantic understanding

sqlglot parses SQL into an Abstract Syntax Tree (AST), allowing precise checks:
- "Is this a SELECT or a DROP?" → check node type
- "Are there comments?" → check string content
- "Is there a LIMIT?" → check for LIMIT node in tree

## Rule Taxonomy

### Block Rules (hard stop)

| Rule | Method | Edge Cases |
|------|--------|------------|
| G001 - DDL/DML | Check `extract_dml_type()` on each AST node | `DROP TABLE IF EXISTS`, `INSERT OR REPLACE` |
| G002 - Transaction | Check SQL string starts with transaction keyword | Mixed case, extra whitespace |
| G003 - Comments | Check string for `--` or `/*` | `'--'` in string literals (safe) |
| G004 - Single statement | Count parsed statements | Accounting for CTEs (single statement with WITH) |
| G005 - Dangerous functions | Walk AST for `load_extension()` | Case-insensitive, function aliases |

### Warn Rules (soft stop)

| Rule | Method | Auto-fix? |
|------|--------|-----------|
| G006 - LIMIT | Check for `exp.Limit` node in tree | Could auto-add `LIMIT 1000` |
| G007 - Nesting depth | Walk AST, count `exp.Subquery` + `exp.With` depth | Warn only |
| G008 - Table join count | Count unique table references | Warn only |

## Rule Registry Pattern

```python
DEFAULT_RULES: list[Rule] = [
    Rule("G001", "Block DDL/DML", check_ddl_dml, action="block"),
    Rule("G002", "Block transactions", check_transaction_control, action="block"),
    ...
]
```

New rules can be added by creating a check function and registering it:

```python
def check_temp_tables(parsed: ParsedQuery) -> RuleResult:
    if any("temp" in t.lower() for t in parsed.tables):
        return RuleResult(passed=False, ...)
    return RuleResult(passed=True, ...)

custom_rules = DEFAULT_RULES + [Rule("G011", "Block temp tables", check_temp_tables)]
validator = SQLValidator(rules=custom_rules)
```

## Testing Strategy

- **White-box**: Test each rule independently with edge cases
- **Black-box**: Test against malicious_queries.json dataset
- **Golden set**: sample_questions.json validates real-world SQL works
- **False positive tracking**: Warnings can be elevated to blocks after analysis