"""Endpoint availability and restart flags based on Action1's reported state."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .const import DOMAIN
from .entity import A1Entity
from .coordinator import is_connected


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    registered = set()

    def discover():
        new = []
        for key in coordinator.data.get("endpoints", {}):
            for kind in ("connectivity", "reboot"):
                identity = (*key, kind)
                if identity not in registered:
                    registered.add(identity)
                    new.append(A1BinarySensor(coordinator, key, kind))
        if new:
            async_add_entities(new)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class A1BinarySensor(A1Entity, BinarySensorEntity):
    def __init__(self, coordinator, key, kind):
        super().__init__(coordinator, key)
        self.kind = kind
        self._attr_unique_id = f"{key[0]}_{key[1]}_{kind}"
        self._attr_name = "Agent connected" if kind == "connectivity" else "Reboot required"
        if kind == "connectivity":
            self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self):
        if self.kind == "connectivity":
            return is_connected(self.device.get("online_status"))
        value = self.device.get("reboot_required")
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            if value.lower() in ("yes", "true", "required"):
                return True
            if value.lower() in ("no", "false", "not_required"):
                return False
        return None
