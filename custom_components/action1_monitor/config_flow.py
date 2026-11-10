"""Action1 API configuration through Home Assistant UI."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from .api import Action1Client, Action1Error
from .const import DOMAIN, REGIONS


class Action1Flow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                api = Action1Client(
                    async_get_clientsession(self.hass),
                    REGIONS[user_input["region"]],
                    user_input["client_id"],
                    user_input["client_secret"],
                )
                orgs = await api.pages("/organizations", max_records=250)
                if not orgs:
                    errors["base"] = "no_organizations"
                else:
                    await self.async_set_unique_id(user_input["client_id"])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Action1 ({user_input['region']})",
                        data=user_input,
                    )
            except (Action1Error, KeyError, ValueError):
                errors["base"] = "cannot_connect"
        schema = vol.Schema({
            vol.Required("region", default="Europe"): vol.In(list(REGIONS)),
            vol.Required("client_id"): str,
            vol.Required("client_secret"): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
