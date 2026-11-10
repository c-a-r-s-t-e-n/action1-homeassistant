"""Shared native Home Assistant endpoint identity."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN


class A1Entity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self.key = key

    @property
    def device(self):
        return self.coordinator.data.get("endpoints", {}).get(self.key, {}).get("device", {})

    @property
    def device_info(self):
        obj = self.device
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.key[0]}/{self.key[1]}")},
            name=obj.get("name") or "Action1 endpoint",
            manufacturer=obj.get("manufacturer") or "Action1 managed endpoint",
            model=obj.get("model") or obj.get("platform"),
            sw_version=obj.get("agent_version"),
        )
