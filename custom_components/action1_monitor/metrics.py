"""Conservative, testable organization-level Action1 security metrics."""


def _items(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        return value["items"]
    return None


def critical_cves(payload):
    """CVSS >= 9.0 is critical; incomplete records are excluded, not guessed."""
    items = _items(payload)
    if items is None:
        return None
    result = 0
    for obj in items:
        if not isinstance(obj, dict):
            continue
        try:
            score = obj.get("cvss_score")
            if score is not None and float(score) >= 9:
                result += 1
        except (TypeError, ValueError):
            continue
    return result


def known_exploited_cves(payload):
    """Count explicit positive CISA KEV markers only."""
    items = _items(payload)
    if items is None:
        return None
    return sum(
        isinstance(obj, dict)
        and str(obj.get("cisa_kev", "")).strip().lower() in ("yes", "true", "1")
        for obj in items
    )


def important_updates(payload):
    items = _items(payload)
    if items is None:
        return None
    known = [
        obj for obj in items
        if isinstance(obj, dict) and obj.get("security_severity") is not None
    ]
    if not known:
        return None
    return sum(
        str(obj.get("security_severity", "")).strip().lower() in ("important", "critical")
        for obj in known
    )
