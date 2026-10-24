import os
import hmac


def auto_outreach_enabled() -> bool:
    """Places cold SMS only when explicitly enabled. Default: gated (false)."""
    return os.getenv("AUTO_OUTREACH", "false").strip().lower() in {"1", "true", "yes", "on"}


def approve_key_ok(provided: str | None) -> bool:
    secret = os.getenv("APPROVE_SECRET") or ""
    if not secret or provided is None:
        return False
    if len(provided) != len(secret):
        return False
    return hmac.compare_digest(provided, secret)
