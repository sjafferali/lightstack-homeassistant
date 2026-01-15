"""
Custom integration to integrate LightStack with Home Assistant.

LightStack is a priority-based alert management system for Inovelli LED switches.

For more details about this integration, please refer to
https://github.com/sjafferali/lightstack-homeassistant
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_ALERT_KEY,
    ATTR_NOTE,
    ATTR_PRIORITY,
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
    PLATFORMS,
    SERVICE_CLEAR_ALERT,
    SERVICE_CLEAR_ALL_ALERTS,
    SERVICE_TRIGGER_ALERT,
    STARTUP_MESSAGE,
)
from .coordinator import LightStackCoordinator
from .websocket import LightStackConnectionError, LightStackWebSocket

_LOGGER = logging.getLogger(__name__)

# Service schemas
TRIGGER_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ALERT_KEY): cv.string,
        vol.Optional(ATTR_PRIORITY): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=5)
        ),
        vol.Optional(ATTR_NOTE): cv.string,
    }
)

CLEAR_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ALERT_KEY): cv.string,
        vol.Optional(ATTR_NOTE): cv.string,
    }
)

CLEAR_ALL_ALERTS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_NOTE): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LightStack from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    # Create WebSocket client
    session = async_get_clientsession(hass)
    websocket = LightStackWebSocket(host, port, session)

    # Create coordinator
    coordinator = LightStackCoordinator(hass, websocket, entry.entry_id)

    # Set up the coordinator
    try:
        success = await coordinator.async_setup()
        if not success:
            raise ConfigEntryNotReady(
                f"Failed to connect to LightStack at {host}:{port}"
            )
    except LightStackConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    # Store coordinator for platforms
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services (only once for the domain)
    await _async_setup_services(hass)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Set up LightStack services."""
    # Check if services are already registered
    if hass.services.has_service(DOMAIN, SERVICE_TRIGGER_ALERT):
        return

    async def handle_trigger_alert(call: ServiceCall) -> None:
        """Handle the trigger_alert service call."""
        alert_key = call.data[ATTR_ALERT_KEY]
        priority = call.data.get(ATTR_PRIORITY)
        note = call.data.get(ATTR_NOTE)

        # Get the first coordinator (services apply to all instances)
        for coordinator in hass.data[DOMAIN].values():
            if isinstance(coordinator, LightStackCoordinator):
                await coordinator.async_trigger_alert(alert_key, priority, note)
                break

    async def handle_clear_alert(call: ServiceCall) -> None:
        """Handle the clear_alert service call."""
        alert_key = call.data[ATTR_ALERT_KEY]
        note = call.data.get(ATTR_NOTE)

        for coordinator in hass.data[DOMAIN].values():
            if isinstance(coordinator, LightStackCoordinator):
                await coordinator.async_clear_alert(alert_key, note)
                break

    async def handle_clear_all_alerts(call: ServiceCall) -> None:
        """Handle the clear_all_alerts service call."""
        note = call.data.get(ATTR_NOTE)

        for coordinator in hass.data[DOMAIN].values():
            if isinstance(coordinator, LightStackCoordinator):
                await coordinator.async_clear_all_alerts(note)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_TRIGGER_ALERT,
        handle_trigger_alert,
        schema=TRIGGER_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ALERT,
        handle_clear_alert,
        schema=CLEAR_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_ALL_ALERTS,
        handle_clear_all_alerts,
        schema=CLEAR_ALL_ALERTS_SCHEMA,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Shutdown coordinator
        coordinator: LightStackCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        # Unregister services if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_TRIGGER_ALERT)
            hass.services.async_remove(DOMAIN, SERVICE_CLEAR_ALERT)
            hass.services.async_remove(DOMAIN, SERVICE_CLEAR_ALL_ALERTS)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
