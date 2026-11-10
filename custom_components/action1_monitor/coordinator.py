"""Action1 monitoring: explicit read-only API calls and conservative caching."""
from datetime import timedelta, datetime, timezone
import logging
from urllib.parse import quote

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Action1Error
from .const import DOMAIN, DEFAULT_INTERVAL, DEEP_REFRESH_CYCLES, MAX_RECORDS

_LOGGER = logging.getLogger(__name__)

ORG_READS = {
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
    "endpoint_status_detail": "endpoints/status/{org}",
}
GLOBAL_READS = {
    "reports": "reports/all",
    "enterprise_usage": "subscription/usage/enterprise",
    "subscription": "subscription/enterprise",
    "audit": "audit/events",
    "scripts": "scripts/all",
}


def normalize_records(payload):
    """Action1 uses ResultPage, lists and occasionally a single object."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return payload["items"]
        if isinstance(payload.get("data"), list):
            return payload["data"]
    return []


def count_or_none(value):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for field in ("total_items", "total", "count"):
            try:
                if field in value:
                    return int(value[field])
            except (ValueError, TypeError):
                continue
        if isinstance(value.get("items"), list):
            return len(value["items"])
    return None


def is_connected(status):
    """Interpret online_status conservatively; unknown is never offline."""
    if isinstance(status, bool):
        return status
    if status is None:
        return None
    value = str(status).strip().lower()
    if value in ("online", "connected", "true", "1"):
        return True
    if value in ("offline", "disconnected", "false", "0"):
        return False
    return None


class Action1Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, client):
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_INTERVAL),
        )
        self.api = client
        self.cycles = 0
        self.deep_cache = {"global": {}, "organizations": {}}
        self.failures = {}
        self.missing_cache = {}

    async def _optional(self, path, params=None):
        try:
            return await self.api.get("/" + path, params)
        except Action1Error as exc:
            self.failures[path.rsplit("/", 1)[-1]] = str(exc)
            return None

    async def _optional_pages(self, path, params=None, max_records=MAX_RECORDS):
        try:
            return await self.api.pages("/" + path, params, max_records)
        except Action1Error as exc:
            self.failures[path.rsplit("/", 1)[-1]] = str(exc)
            return None

    async def _async_update_data(self):
        self.cycles += 1
        deep = self.cycles == 1 or self.cycles % DEEP_REFRESH_CYCLES == 0
        try:
            organizations = await self.api.pages(
                "/organizations", max_records=250
            )
            endpoint_index = {}
            summary = {
                "organizations": {},
                "global": self.deep_cache["global"],
                "errors": self.failures,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if deep:
                for name, path in GLOBAL_READS.items():
                    data = await self._optional(path)
                    if data is not None:
                        self.deep_cache["global"][name] = data

            for org in organizations:
                if not isinstance(org, dict) or not org.get("id"):
                    continue
                org_id = str(org["id"])
                safe_id = quote(org_id, safe="")
                endpoint_list = await self.api.pages(
                    f"/endpoints/managed/{safe_id}",
                    {"fields": "*"},
                    max_records=MAX_RECORDS,
                )
                deep_org = self.deep_cache["organizations"].setdefault(
                    org_id, {}
                )
                if deep:
                    for name, template in ORG_READS.items():
                        route = template.format(org=safe_id)
                        if name in (
                            "vulnerabilities", "updates", "software",
                            "automation_instances", "logs",
                        ):
                            data = await self._optional_pages(
                                route, max_records=MAX_RECORDS
                            )
                        else:
                            data = await self._optional(route)
                        if data is not None:
                            deep_org[name] = data
                summary["organizations"][org_id] = {
                    "meta": org,
                    "endpoint_count": len(endpoint_list),
                    "online_count": sum(
                        is_connected(x.get("online_status")) is True
                        for x in endpoint_list if isinstance(x, dict)
                    ),
                    "unknown_connection_count": sum(
                        is_connected(x.get("online_status")) is None
                        for x in endpoint_list if isinstance(x, dict)
                    ),
                    "deep": deep_org,
                }
                for endpoint in endpoint_list:
                    if not isinstance(endpoint, dict) or not endpoint.get("id"):
                        continue
                    key = (org_id, str(endpoint["id"]))
                    endpoint_index[key] = {
                        "organization": org,
                        "device": endpoint,
                        "org_id": org_id,
                        "endpoint_id": str(endpoint["id"]),
                    }

            # Rotate expensive individual missing-update queries across devices.
            ordered_keys = sorted(endpoint_index)
            if ordered_keys:
                start = ((self.cycles - 1) * 5) % len(ordered_keys)
                selected = [
                    ordered_keys[(start + i) % len(ordered_keys)]
                    for i in range(min(5, len(ordered_keys)))
                ]
                for org_id, endpoint_id in selected:
                    safe_org = quote(org_id, safe="")
                    safe_endpoint = quote(endpoint_id, safe="")
                    result = await self._optional_pages(
                        f"endpoints/managed/{safe_org}/{safe_endpoint}/missing-updates",
                        max_records=300,
                    )
                    if result is not None:
                        self.missing_cache[(org_id, endpoint_id)] = result

            summary["missing_updates"] = {
                key: value
                for key, value in self.missing_cache.items()
                if key in endpoint_index
            }
            summary["endpoints"] = endpoint_index
            return summary
        except (Action1Error, KeyError, TypeError, ValueError) as exc:
            raise UpdateFailed(
                "Unable to load Action1 organization/endpoint inventory"
            ) from exc
