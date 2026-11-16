"""Organization summary and endpoint sensors with explicit API field mapping."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .entity import A1Entity
from .coordinator import count_or_none
from .model import simple_scalar, report_total

ENDPOINT_FIELDS = {
    "status": ("Agent status", "status", None),
    "online_status": ("Online status", "online_status", None),
    "device_name": ("Device name", "device_name", None),
    "architecture": ("Architecture", "architecture", None),
    "manufacturer": ("Manufacturer", "manufacturer", None),
    "cpu_name": ("CPU", "CPU_name", None),
    "cpu_size": ("CPU cores", "CPU_size", None),
    "serial": ("Serial number", "serial", None),
    "last_seen": ("Last seen", "last_seen", None),
    "os": ("Operating system", "OS", None),
    "platform": ("Platform", "platform", None),
    "agent_version": ("Agent version", "agent_version", None),
    "agent_install_date": ("Agent install date", "agent_install_date", None),
    "last_boot_time": ("Last boot", "last_boot_time", None),
    "update_status": ("Update status", "update_status", None),
    "vulnerability_status": ("Vulnerability status", "vulnerability_status", None),
    "subscription_status": ("Subscription status", "subscription_status", None),
    "critical_updates": ("Missing critical updates", "missing_critical_updates", None),
    "other_updates": ("Missing other updates", "missing_other_updates", None),
    "ram": ("Memory", "RAM", None),
    "user": ("Last reported user", "user", None),
    "comment": ("Comment", "comment", None),
    "missing_update_details": ("Missing update records", "missing_update_details", None),
    "vulnerability_reported": ("Vulnerabilities reported", "vulnerabilities", None),
    "missing_updates_reported": ("Missing updates reported", "missing_updates", None),
}
ORG_FIELDS = {
    "endpoints": ("Managed endpoints", "endpoint_count"),
    "online": ("Online endpoints", "online_count"),
    "offline": ("Offline endpoints", "offline_count"),
    "connection_unknown": ("Unknown connection state", "unknown_connection_count"),
    "endpoint_groups": ("Endpoint groups", "endpoint_groups"),
    "vulnerabilities": ("Known vulnerabilities", "vulnerabilities"),
    "updates": ("Missing update catalog items", "updates"),
    "software": ("Installed software report metadata", "software"),
    "automation_schedules": ("Automation schedules", "automation_schedules"),
    "automation_instances": ("Automation instances", "automation_instances"),
    "logs": ("Diagnostic log entries", "logs"),
    "deployers": ("Deployers", "deployers"),
    "critical_cves": ("Critical CVEs (CVSS 9+)", "critical_cves"),
    "known_exploited": ("Known exploited CVEs", "known_exploited"),
    "important_updates": ("Critical / important update items", "important_updates"),
    "software_errors": ("Software inventory errors", "software_errors"),
    "high_cves": ("High CVEs (CVSS 7–8.9)", "high_cves"),
    "severity_unknown": ("CVEs without severity", "unknown_severity"),
    "vulnerability_coverage": ("CVE detail coverage", "vulnerability_coverage"),
    "usage_active": ("Active subscription endpoints", "current_active_endpoint_count"),
    "usage_inactive": ("Inactive subscription endpoints", "current_inactive_endpoint_count"),
    "usage_monthly_avg": ("Monthly average endpoints", "monthly_average_endpoint_count"),
}
GLOBAL_FIELDS = {
    "organizations": "Organizations",
    "licensed_endpoints": "Licensed endpoints",
    "free_endpoints": "Free endpoints",
    "actual_endpoints": "Subscription actual endpoints",
    "license_expires": "License expires",
    "license_status": "License status",
    "license_type": "License type",
    "subscription_exceeded": "License limit exceeded",
    "enterprise_active": "Enterprise active endpoints",
    "enterprise_inactive": "Enterprise inactive endpoints",
    "enterprise_monthly_average": "Enterprise monthly average endpoints",
    "last_deep_report": "Last detailed report",
    "reports": "Available reports",
    "scripts": "Script library entries",
    "audit": "Audit records",
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    registered = set()

    def discover():
        new = []
        for name in GLOBAL_FIELDS:
            key = ("global", name)
            if key not in registered:
                registered.add(key)
                new.append(A1GlobalSensor(coordinator, name))
        for org_id in coordinator.data.get("organizations", {}):
            for field in ORG_FIELDS:
                key = (org_id, field)
                if key not in registered:
                    registered.add(key)
                    new.append(A1OrganizationSensor(coordinator, org_id, field))
        for endpoint_key in coordinator.data.get("endpoints", {}):
            for field in ENDPOINT_FIELDS:
                key = (*endpoint_key, field)
                if key not in registered:
                    registered.add(key)
                    new.append(A1EndpointSensor(coordinator, endpoint_key, field))
        if new:
            async_add_entities(new)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class A1EndpointSensor(A1Entity, SensorEntity):
    def __init__(self, coordinator, key, field):
        super().__init__(coordinator, key)
        self.field = field
        label, _, unit = ENDPOINT_FIELDS[field]
        self._attr_name = label
        self._attr_unique_id = f"{key[0]}_{key[1]}_{field}"
        if unit:
            self._attr_native_unit_of_measurement = unit
        if field in (
            "agent_version", "platform", "agent_install_date",
            "comment", "user", "serial", "architecture", "cpu_size",
            "subscription_status",
        ):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if field in (
            "comment", "user", "serial", "agent_install_date",
            "subscription_status", "device_name", "architecture",
            "manufacturer", "cpu_size",
        ):
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        api_key = ENDPOINT_FIELDS[self.field][1]
        if api_key in ("missing_critical_updates", "missing_other_updates"):
            # These are officially documented extended fields returned with
            # /endpoints/managed/{org}?fields=*; not derived from patch names.
            raw = self.device.get(api_key)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0:
                return raw
            if isinstance(raw, str) and raw.isdecimal():
                return int(raw)
            return None
        if api_key == "missing_update_details":
            value = self.coordinator.data.get("missing_updates", {}).get(self.key)
            return count_or_none(value) if value is not None else None
        value = self.device.get(api_key)
        if self.field in ("vulnerability_reported", "missing_updates_reported"):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return int(value)
            return report_total(value)
        return simple_scalar(value)


class A1OrganizationSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, org_id, field):
        super().__init__(coordinator)
        self.org_id = org_id
        self.field = field
        self._attr_unique_id = f"{org_id}_{field}_summary"
        self._attr_name = ORG_FIELDS[field][0]

    @property
    def device_info(self):
        org = self.coordinator.data.get("organizations", {}).get(self.org_id, {})
        return DeviceInfo(
            identifiers={(DOMAIN, f"organization:{self.org_id}")},
            name=f"Action1 - {org.get('meta', {}).get('name', 'Organization')}",
            manufacturer="Action1",
            model="Organization",
        )

    @property
    def available(self):
        return (
            self.coordinator.last_update_success
            and self.org_id in self.coordinator.data.get("organizations", {})
        )

    @property
    def native_value(self):
        info = self.coordinator.data.get("organizations", {}).get(self.org_id, {})
        field = ORG_FIELDS[self.field][1]
        if field == "offline_count":
            return max(
                0, info.get("endpoint_count", 0)
                - info.get("online_count", 0)
                - info.get("unknown_connection_count", 0),
            )
        if field in ("endpoint_count", "online_count", "unknown_connection_count"):
            return info.get(field)
        deep = info.get("deep", {})
        if field in ("critical_cves", "high_cves", "known_exploited",
                     "unknown_severity", "vulnerability_coverage"):
            report = deep.get("vulnerabilities")
            if not isinstance(report, dict):
                return None
            if field == "vulnerability_coverage":
                return "Complete" if report.get("complete") else "Partial"
            if report.get("complete") is not True:
                return None
            return report.get(field)
        if field == "important_updates":
            return None  # Severity field not verified in live report schema.
        if self.field.startswith("usage_"):
            report = deep.get("usage")
            return report.get(field) if isinstance(report, dict) else None
        return count_or_none(deep.get(field))


class A1GlobalSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, field):
        super().__init__(coordinator)
        self.field = field
        self._attr_name = GLOBAL_FIELDS[field]
        self._attr_unique_id = f"action1_global_{field}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "enterprise")},
            name="Action1 Enterprise",
            manufacturer="Action1",
            model="Cloud API",
        )

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        data = self.coordinator.data
        if self.field == "organizations":
            return len(data.get("organizations", {}))
        if self.field == "last_deep_report":
            return data.get("deep_report_updated_at")
        license_keys = {
            "licensed_endpoints": "licensed_endpoint_count",
            "free_endpoints": "free_endpoint_count",
            "actual_endpoints": "actual_endpoint_count",
            "license_expires": "license_expires",
            "license_status": "license_status",
            "license_type": "license_type",
            "subscription_exceeded": "exceeded",
        }
        usage_keys = {
            "enterprise_active": "current_active_endpoint_count",
            "enterprise_inactive": "current_inactive_endpoint_count",
            "enterprise_monthly_average": "monthly_average_endpoint_count",
        }
        if self.field in license_keys:
            obj = data.get("global", {}).get("subscription")
            if not isinstance(obj, dict):
                return None
            value = obj.get(license_keys[self.field])
            if self.field == "subscription_exceeded" and isinstance(value, bool):
                return "Yes" if value else "No"
            return value
        if self.field in usage_keys:
            obj = data.get("global", {}).get("enterprise_usage")
            return obj.get(usage_keys[self.field]) if isinstance(obj, dict) else None
        return count_or_none(data.get("global", {}).get(self.field))
