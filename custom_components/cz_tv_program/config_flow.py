"""Config flow for Czech TV Program integration."""

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import (
    CT_CHANNELS,
    DEFAULT_SOURCE,
    DEFAULT_USERNAME,
    DEFAULT_XMLTV_URL,
    DOMAIN,
    SOURCE_CT,
    SOURCE_XMLTV,
    XMLTV_CHANNELS,
)

_LOGGER = logging.getLogger(__name__)


class CzTVProgramConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Czech TV Program."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - select source."""
        if user_input is not None:
            self.source = user_input.get("source", DEFAULT_SOURCE)
            return await self.async_step_channels()

        data_schema = vol.Schema(
            {
                vol.Required("source", default=DEFAULT_SOURCE): vol.In(
                    {
                        SOURCE_CT: "Česká televize (ČT1, ČT2, ČT24, ...)",
                        SOURCE_XMLTV: "XMLTV - Prima, Nova a další",
                    }
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_channels(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle channel selection step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id("cz_tv_program")
            self._abort_if_unique_id_configured()

            data = {
                "source": self.source,
                "channels": user_input["channels"],
            }

            if self.source == SOURCE_CT:
                data["username"] = user_input.get("username", DEFAULT_USERNAME)
            elif self.source == SOURCE_XMLTV:
                data["xmltv_url"] = user_input.get("xmltv_url", DEFAULT_XMLTV_URL)

            return self.async_create_entry(
                title=f"TV Program ({self.source.upper()})",
                data=data,
                options={f"{DOMAIN}_OPTIONS": user_input["channels"]},
            )

        # Build channel options based on source
        if self.source == SOURCE_XMLTV:
            channel_options = dict(
                sorted(XMLTV_CHANNELS.items(), key=lambda kv: kv[1].casefold())
            )
            data_schema = vol.Schema(
                {
                    vol.Optional("xmltv_url", default=DEFAULT_XMLTV_URL): str,
                    vol.Required(
                        "channels", default=list(channel_options.keys())[:5]
                    ): cv.multi_select(channel_options),
                }
            )
        else:
            channel_options = dict(
                sorted(CT_CHANNELS.items(), key=lambda kv: kv[1].casefold())
            )
            data_schema = vol.Schema(
                {
                    vol.Optional("username", default=DEFAULT_USERNAME): str,
                    vol.Required(
                        "channels", default=list(channel_options)
                    ): cv.multi_select(channel_options),
                }
            )

        return self.async_show_form(
            step_id="channels",
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

        # Get channel options based on source
        source = entry.data.get("source", SOURCE_CT)
        if source == SOURCE_XMLTV:
            channel_options = dict(
                sorted(XMLTV_CHANNELS.items(), key=lambda kv: kv[1].casefold())
            )
        else:
            channel_options = dict(
                sorted(CT_CHANNELS.items(), key=lambda kv: kv[1].casefold())
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
