"""Sanitized, structural Action1 diagnostics for Home Assistant.

Never emit account identifiers, endpoint names, credentials, software titles,
vulnerability identifiers, serial numbers, raw audit entries or log messages.
"""

from .const import DOMAIN


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    organizations = data.get("organizations") or {}
    global_reports = data.get("global") or {}
    return {
        "integration": DOMAIN,
        "version": "1.0.0",
        "region": entry.data.get("region"),
        "organization_count": len(organizations),
        "endpoint_count": len(data.get("endpoints") or {}),
        "organization_endpoint_counts": sorted(
            obj.get("endpoint_count", 0)
            for obj in organizations.values()
            if isinstance(obj, dict)
        ),
        "organization_deep_report_categories": sorted({
            key
            for obj in organizations.values()
            if isinstance(obj, dict)
            for key in (obj.get("deep") or {})
        }),
        "global_report_categories": sorted(global_reports),
        "endpoints_with_missing_update_totals": len(data.get("missing_updates") or {}),
        "report_errors_by_category": sorted({
            str(path).split("/")[0]
            for path in (data.get("errors") or {})
        }),
        "last_inventory_sync": data.get("updated_at"),
        "last_deep_report": data.get("deep_report_updated_at"),
        "caution": "Structural metadata only; no individual endpoint data included.",
    }
