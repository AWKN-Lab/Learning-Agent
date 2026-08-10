from __future__ import annotations


class RuntimeGovernanceError(Exception):
    code = "runtime_governance_error"


class SessionUnauthorized(RuntimeGovernanceError):
    code = "session_unauthorized"


class SessionExpired(RuntimeGovernanceError):
    code = "session_expired"


class RateLimitExceeded(RuntimeGovernanceError):
    code = "rate_limit_exceeded"
