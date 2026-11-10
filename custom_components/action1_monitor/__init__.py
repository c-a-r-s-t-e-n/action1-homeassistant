"""Action1 Monitor read-only integration."""
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import Action1Client
from .coordinator import Action1Coordinator
from .const import DOMAIN, REGIONS

PLATFORMS = ("sensor", "binary_sensor")


async def async_setup_entry(hass, entry):
    client = Action1Client(
        async_get_clientsession(hass),
        REGIONS[entry.data["region"]],
        entry.data["client_id"],
        entry.data["client_secret"],
    )
    coordinator = Action1Coordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
