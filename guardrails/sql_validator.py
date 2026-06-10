from dataclasses import dataclass, field

from guardrails.parser import parse_sql
from guardrails.rules import Rule, RuleResult, DEFAULT_RULES
from guardrails.exceptions import GuardrailsError


@dataclass
class ValidationResult:
    valid: bool
    sql: str
    errors: list[GuardrailsError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rule_results: list[RuleResult] = field(default_factory=list)


class SQLValidator:
    def __init__(self, rules: list[Rule] | None = None):
        self.rules = rules or DEFAULT_RULES

    def validate(self, sql: str) -> ValidationResult:
        parsed = parse_sql(sql)

        if not parsed.is_valid:
            return ValidationResult(
                valid=False,
                sql=sql,
                errors=[GuardrailsError(f"Parse error: {parsed.errors[0]}", "parse_error")],
                rule_results=[],
            )

        errors: list[GuardrailsError] = []
        warnings: list[str] = []
        results: list[RuleResult] = []

        for rule in self.rules:
            result = rule.check_fn(parsed)
            results.append(result)

            if not result.passed:
                if rule.action == "block":
                    errors.append(result.error)
                elif rule.action == "warn":
                    warnings.append(result.message)

        return ValidationResult(
            valid=len(errors) == 0,
            sql=sql,
            errors=errors,
            warnings=warnings,
            rule_results=results,
        )


validator = SQLValidator()