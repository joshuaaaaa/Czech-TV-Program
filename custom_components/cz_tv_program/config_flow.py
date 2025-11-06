"""Config flow for Czech TV Program integration."""

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import AVAILABLE_CHANNELS, DEFAULT_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CzTVProgramConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Czech TV Program."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate and create entry
            await self.async_set_unique_id("cz_tv_program")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Czech TV Program",
                data={
                    "username": user_input.get("username", DEFAULT_USERNAME),
                    "channels": user_input["channels"],
                },
                options={f"{DOMAIN}_OPTIONS": user_input["channels"]},
            )

        # Build multi-select options for channels
        channel_options = dict(
            sorted(AVAILABLE_CHANNELS.items(), key=lambda kv: kv[1].casefold())
        )

        # OPRAVA: Přidán username field
        data_schema = vol.Schema(
            {
                vol.Optional("username", default=DEFAULT_USERNAME): str,
                vol.Required(
                    "channels", default=list(channel_options)
                ): cv.multi_select(channel_options),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CzTVProgramOptionsFlow(config_entry)


class CzTVProgramOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Czech TV Program."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data={f"{DOMAIN}_OPTIONS": user_input["channels"]}
            )

        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        set_options = sorted(
            entry.options.get(f"{DOMAIN}_OPTIONS", []), key=str.casefold
        )

        channel_options = dict(
            sorted(AVAILABLE_CHANNELS.items(), key=lambda kv: kv[1].casefold())
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("channels", default=set_options): cv.multi_select(
                        channel_options
                    ),
                }
            ),
        )
