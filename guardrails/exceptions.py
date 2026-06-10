class GuardrailsError(Exception):
    reason: str

    def __init__(self, message: str, reason: str | None = None) -> None:
        self.reason = reason or "unknown"
        super().__init__(message)


class SecurityError(GuardrailsError):
    def __init__(self, message: str, reason: str = "security_violation") -> None:
        super().__init__(message, reason)


class SyntaxError_(GuardrailsError):
    def __init__(self, message: str, reason: str = "syntax_error") -> None:
        super().__init__(message, reason)


class ComplexityError(GuardrailsError):
    def __init__(self, message: str, reason: str = "complexity_limit") -> None:
        super().__init__(message, reason)