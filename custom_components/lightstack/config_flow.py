"""Config flow for LightStack integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DOMAIN,
    NAME,
)
from .websocket import LightStackConnectionError, LightStackWebSocket

_LOGGER = logging.getLogger(__name__)


class LightStackConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LightStack."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        self._errors = {}

        if user_input is not None:
            # Check if already configured with this host/port
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            # Test the connection
            if await self._test_connection(
                user_input[CONF_HOST], user_input[CONF_PORT]
            ):
                return self.async_create_entry(
                    title=f"{NAME} ({user_input[CONF_HOST]}:{user_input[CONF_PORT]})",
                    data=user_input,
                )
            self._errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=self._errors,
        )

    async def _test_connection(self, host: str, port: int) -> bool:
        """Test if we can connect to the LightStack server."""
        try:
            session = async_create_clientsession(self.hass)
            websocket = LightStackWebSocket(host, port, session)

            # Try to connect
            await websocket.connect()

            # Disconnect after successful test
            await websocket.disconnect()

            return True
        except LightStackConnectionError as err:
            _LOGGER.error("Failed to connect to LightStack: %s", err)
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected error testing LightStack connection: %s", err)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LightStackOptionsFlowHandler:
        """Get the options flow for this handler."""
        return LightStackOptionsFlowHandler(config_entry)


class LightStackOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle LightStack options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
