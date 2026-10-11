class SessionRuleError(Exception):
    """A work session / activity / break rule was not met.

    Carries the exact payload and status the endpoint answers with, so moving the
    rules out of the views does not change any response. The views turn it into
    the standard error envelope (SessionRuleErrorMixin).
    """

    def __init__(self, payload, status_code: int = 400, code: str = "business_rule"):
        super().__init__(str(payload))
        self.payload = payload
        self.status_code = status_code
        self.code = code