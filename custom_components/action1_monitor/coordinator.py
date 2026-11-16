"""Bounded, read-only Action1 monitoring coordinated across all entities."""
from datetime import datetime, timedelta, timezone
import logging
from urllib.parse import quote

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Action1Error
from .const import DOMAIN, DEFAULT_INTERVAL, DEEP_REFRESH_CYCLES
from .model import endpoint_health, report_total, report_items, severity_summary, simple_scalar

_LOGGER = logging.getLogger(__name__)
MAX_ORGANIZATIONS = 250
MAX_ENDPOINTS = 5000
MAX_VULNERABILITY_DETAILS = 1000
MAX_MISSING_UPDATE_DETAILS = 300

# These are documented GET routes verified by sanitized API schema probes.
ORG_REPORTS = {
    "endpoint_groups": "endpoints/groups/{org}",
    "vulnerabilities": "vulnerabilities/{org}",
    "updates": "updates/{org}",
    "software": "installed-software/{org}/data",
    "automation_schedules": "automations/schedules/{org}",
    "automation_instances": "automations/instances/{org}",
    "logs": "logs/{org}",
    "deployers": "endpoints/deployers/{org}",
    "usage": "subscription/usage/organizations/{org}",
    "software_errors": "installed-software/{org}/errors",
}
GLOBAL_REPORTS = {
    "reports": "reports/all",
    "enterprise_usage": "subscription/usage/enterprise",
    "subscription": "subscription/enterprise",
    "audit": "audit/events",
    "scripts": "scripts/all",
}
USAGE_FIELDS = (
    "current_active_endpoint_count",
    "current_inactive_endpoint_count",
    "monthly_average_endpoint_count",
)
LICENSE_FIELDS = (
    "actual_endpoint_count", "licensed_endpoint_count", "free_endpoint_count",
    "license_expires", "license_status", "license_type", "exceeded", "MSP",
)


def count_or_none(value):
    """Preserve unknown instead of converting a failed query to zero."""
    return report_total(value)


def is_connected(status):
    """Compatibility facade; never infer offline from an unrecognized value."""
    return endpoint_health(status)


class Action1Coordinator(DataUpdateCoordinator):
    """Fast inventory + staggered deep reporting with bounded memory."""

    def __init__(self, hass, client):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_INTERVAL),
        )
        self.api = client
        self.cycles = 0
        self.deep_cache = {"global": {}, "organizations": {}}
        self.failures = {}
        self.missing_cache = {}
        self._report_times = {}

    async def _optional(self, path, params=None):
        try:
            result = await self.api.get("/" + path, params)
        except Action1Error:
            self.failures[path] = "request_failed"
            _LOGGER.debug("Optional Action1 report unavailable: %s", path.split("/")[-1])
            return None
        self.failures.pop(path, None)
        return result

    async def _optional_pages(self, path, params=None, max_records=1000):
        try:
            result = await self.api.pages("/" + path, params, max_records=max_records)
        except Action1Error:
            self.failures[path] = "request_failed"
            _LOGGER.debug("Optional Action1 collection unavailable: %s", path.split("/")[-1])
            return None
        self.failures.pop(path, None)
        return result

    @staticmethod
    def _safe_scalars(payload, names):
        if not isinstance(payload, dict):
            return {}
        return {key: simple_scalar(payload.get(key)) for key in names if key in payload}

    async def _read_summary(self, path):
        # First page is enough for exact total_items; never retrieve raw
        # scripts, user audit events or full software inventory into memory.
        payload = await self._optional(path, {"from": 0, "limit": 1})
        return {"total_items": count_or_none(payload)} if payload is not None else None

    async def _read_vulnerabilities(self, path):
        first = await self._optional(path, {"from": 0, "limit": 100})
        if first is None:
            return None
        total = report_total(first)
        sample = report_items(first)
        # Only publish severity totals if every reported row was examined.
        if total is not None and total > MAX_VULNERABILITY_DETAILS:
            return {"total_items": total, "complete": False, "sampled": len(sample)}
        if total is not None and total > len(sample):
            records = await self._optional_pages(
                path, max_records=MAX_VULNERABILITY_DETAILS
            )
            if records is None:
                return {"total_items": total, "complete": False, "sampled": len(sample)}
            sample = records
        complete = total is not None and len(sample) >= total
        result = {
            "total_items": total,
            "complete": complete,
            "sampled": len(sample),
        }
        if complete:
            result.update(severity_summary(sample))
        return result

    async def _read_deep(self, organizations):
        # Organization-level data is refreshed at a much slower rate, with
        # cloud totals rather than large lists of private records.
        for name, path in GLOBAL_REPORTS.items():
            if name == "subscription":
                result = await self._optional(path)
                safe = self._safe_scalars(result, LICENSE_FIELDS)
            elif name == "enterprise_usage":
                result = await self._optional(path)
                safe = self._safe_scalars(result, USAGE_FIELDS)
            else:
                safe = await self._read_summary(path)
            if safe is not None:
                self.deep_cache["global"][name] = safe

        for org in organizations:
            if not isinstance(org, dict) or org.get("id") is None:
                continue
            org_id = str(org["id"])
            dest = self.deep_cache["organizations"].setdefault(org_id, {})
            safe_id = quote(org_id, safe="")
            for name, template in ORG_REPORTS.items():
                path = template.format(org=safe_id)
                if name == "usage":
                    result = await self._optional(path)
                    safe = self._safe_scalars(result, USAGE_FIELDS)
                elif name == "vulnerabilities":
                    safe = await self._read_vulnerabilities(path)
                else:
                    safe = await self._read_summary(path)
                if safe is not None:
                    dest[name] = safe
        self._report_times["deep"] = datetime.now(timezone.utc).isoformat()

    async def _async_update_data(self):
        self.cycles += 1
        # Avoid long initial setup; first obtain all endpoint inventory.
        deep = self.cycles >= 2 and (self.cycles - 2) % DEEP_REFRESH_CYCLES == 0
        try:
            organizations = await self.api.pages(
                "/organizations", max_records=MAX_ORGANIZATIONS
            )
            endpoint_index = {}
            org_index = {}
            if deep:
                await self._read_deep(organizations)

            for org in organizations:
                if not isinstance(org, dict) or org.get("id") is None:
                    continue
                org_id = str(org["id"])
                safe_id = quote(org_id, safe="")
                endpoints = await self.api.pages(
                    f"/endpoints/managed/{safe_id}",
                    {"fields": "*"},
                    max_records=MAX_ENDPOINTS,
                )
                valid = [
                    row for row in endpoints
                    if isinstance(row, dict) and row.get("id") is not None
                ]
                states = [
                    is_connected(row.get("online_status"))
                    for row in valid
                ]
                org_index[org_id] = {
                    "meta": {"name": org.get("name"), "id": org_id},
                    "endpoint_count": len(valid),
                    "online_count": sum(s is True for s in states),
                    "unknown_connection_count": sum(s is None for s in states),
                    "deep": self.deep_cache["organizations"].get(org_id, {}),
                }
                for endpoint in valid:
                    key = (org_id, str(endpoint["id"]))
                    endpoint_index[key] = {
                        "device": endpoint,
                        "organization": org_index[org_id]["meta"],
                    }

            # Rotate up to five cheap total-only queries; do not download
            # 300 potentially sensitive KB descriptions per device.
            keys = sorted(endpoint_index)
            if keys:
                start = ((self.cycles - 1) * 5) % len(keys)
                for step in range(min(5, len(keys))):
                    org_id, endpoint_id = keys[(start + step) % len(keys)]
                    safe_org = quote(org_id, safe="")
                    safe_endpoint = quote(endpoint_id, safe="")
                    path = (
                        f"endpoints/managed/{safe_org}/{safe_endpoint}/missing-updates"
                    )
                    payload = await self._optional(
                        path, {"from": 0, "limit": 1}
                    )
                    if payload is not None:
                        self.missing_cache[(org_id, endpoint_id)] = {
                            "total_items": report_total(payload)
                        }
            self.missing_cache = {
                key: value for key, value in self.missing_cache.items()
                if key in endpoint_index
            }
            return {
                "organizations": org_index,
                "endpoints": endpoint_index,
                "global": self.deep_cache["global"],
                "missing_updates": dict(self.missing_cache),
                "errors": dict(self.failures),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "deep_report_updated_at": self._report_times.get("deep"),
            }
        except (Action1Error, KeyError, TypeError, ValueError) as exc:
            raise UpdateFailed(
                "Unable to update Action1 organization and endpoint inventory"
            ) from exc
