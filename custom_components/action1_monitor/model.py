"""Small, privacy-aware Action1 reporting helpers.

The API returns ResultPage objects containing counts and records. We never
interpret a missing report as a successful report containing zero records.
"""


def report_total(payload):
    """Authoritative total_items if present; otherwise count returned rows."""
    if isinstance(payload, dict):
        try:
            if payload.get("total_items") is not None:
                return max(0, int(payload["total_items"]))
        except (TypeError, ValueError):
            return None
        items = payload.get("items")
        return len(items) if isinstance(items, list) else None
    return len(payload) if isinstance(payload, list) else None


def report_items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    return []


def simple_scalar(value):
    """Do not write structured API inventory objects into scalar HA state."""
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    if isinstance(value, str) and len(value) > 255:
        return value[:255]
    return value


def conservative_bool(value):
    if isinstance(value, bool):
        return value
    if value == 1:
        return True
    if value == 0:
        return False
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "yes", "1", "required", "on"):
            return True
        if v in ("false", "no", "0", "not_required", "off"):
            return False
    return None


def severity_summary(items):
    """Separate confirmed critical CVSS findings from unknown severity."""
    critical = high = known_exploited = unknown = 0
    for record in items:
        if not isinstance(record, dict):
            continue
        try:
            score = float(record["cvss_score"])
            if not 0 <= score <= 10:
                raise ValueError("invalid CVSS")
        except (ValueError, TypeError, KeyError):
            unknown += 1
        else:
            critical += score >= 9.0
            high += 7.0 <= score < 9.0
        known_exploited += conservative_bool(record.get("cisa_kev")) is True
    return {
        "critical_cves": int(critical),
        "high_cves": int(high),
        "known_exploited": int(known_exploited),
        "unknown_severity": unknown,
        "evaluated": len(items),
    }


def endpoint_health(online_status, last_seen=None):
    """Keep unknown online-status values distinct from offline devices."""
    if isinstance(online_status, bool):
        return online_status
    if online_status is None:
        return None
    value = str(online_status).strip().lower()
    if value in ("online", "connected", "true", "1"):
        return True
    if value in ("offline", "disconnected", "false", "0"):
        return False
    return None


def nonnegative_count(value):
    """Return an explicit API count, never treating bools as integers."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    return None
