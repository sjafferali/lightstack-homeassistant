"""DataUpdateCoordinator for LightStack integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    RECONNECT_INTERVAL,
    WS_EVENT_ALERT_CLEARED,
    WS_EVENT_ALERT_TRIGGERED,
    WS_EVENT_ALL_ALERTS_CLEARED,
    WS_EVENT_CURRENT_ALERT_CHANGED,
)
from .websocket import LightStackConnectionError, LightStackWebSocket

_LOGGER = logging.getLogger(__name__)


@dataclass
class LightStackAlert:
    """Representation of a LightStack alert."""

    alert_key: str
    is_active: bool = False
    effective_priority: int = 3
    priority: int | None = None
    last_triggered_at: str | None = None
    name: str | None = None
    description: str | None = None
    default_priority: int = 3
    led_color: int | None = None
    led_effect: str | None = None
    led_brightness: int | None = None
    led_duration: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LightStackAlert:
        """Create an alert from a dictionary.

        Handles both flat data (from WebSocket events) and nested config data
        (from REST API responses where config fields are nested in 'config' key).
        """
        # Handle nested config data (from REST API responses)
        # Use None as default (not {}) so empty dict doesn't cause issues
        # (empty dict is truthy in Python, None is falsy)
        config = data.get("config")

        # Helper to get value from config (if present) or top-level data
        def get_field(field_name: str, default: Any = None) -> Any:
            if config and field_name in config:
                return config.get(field_name, default)
            return data.get(field_name, default)

        return cls(
            alert_key=data.get("alert_key", ""),
            is_active=data.get("is_active", False),
            effective_priority=data.get("effective_priority", 3),
            priority=data.get("priority"),
            last_triggered_at=data.get("last_triggered_at"),
            name=get_field("name"),
            description=get_field("description"),
            default_priority=get_field("default_priority", 3),
            led_color=get_field("led_color"),
            led_effect=get_field("led_effect"),
            led_brightness=get_field("led_brightness"),
            led_duration=get_field("led_duration"),
        )


@dataclass
class LightStackState:
    """Representation of LightStack state."""

    is_all_clear: bool = True
    current_alert: LightStackAlert | None = None
    active_count: int = 0
    active_alerts: list[LightStackAlert] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LightStackState:
        """Create state from a dictionary."""
        current_alert_data = data.get("current_alert")
        current_alert = (
            LightStackAlert.from_dict(current_alert_data)
            if current_alert_data
            else None
        )

        active_alerts_data = data.get("active_alerts", [])
        active_alerts = [LightStackAlert.from_dict(a) for a in active_alerts_data]

        return cls(
            is_all_clear=data.get("is_all_clear", True),
            current_alert=current_alert,
            active_count=data.get("active_count", 0),
            active_alerts=active_alerts,
        )


class LightStackCoordinator(DataUpdateCoordinator[LightStackState]):
    """Coordinator for LightStack WebSocket data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        websocket: LightStackWebSocket,
        entry_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # No update_interval - we use push updates via WebSocket
        )
        self.websocket = websocket
        self.entry_id = entry_id
        self._remove_listener: callable | None = None
        self._maintain_task: asyncio.Task | None = None
        self._initial_state: LightStackState | None = None

    async def async_setup(self) -> bool:
        """Set up the coordinator.

        Returns:
            True if setup was successful.
        """
        try:
            # Connect and get initial state
            initial_data = await self.websocket.connect()
            self._initial_state = LightStackState.from_dict(initial_data)
            self.async_set_updated_data(self._initial_state)

            # Add event listener
            self._remove_listener = self.websocket.add_listener(self._handle_event)

            # Start listening for messages
            await self.websocket.start_listening()

            # Start connection maintenance task
            self._maintain_task = self.hass.async_create_background_task(
                self._maintain_connection(),
                "lightstack_connection_maintainer",
            )

            return True

        except LightStackConnectionError as err:
            _LOGGER.error("Failed to connect to LightStack: %s", err)
            return False

    async def _maintain_connection(self) -> None:
        """Maintain the WebSocket connection."""
        while True:
            await asyncio.sleep(RECONNECT_INTERVAL)

            if not self.websocket.connected:
                _LOGGER.info("LightStack disconnected, attempting reconnection...")
                try:
                    initial_data = await self.websocket.reconnect()
                    if initial_data is not None:
                        _LOGGER.info("Successfully reconnected to LightStack")
                        self.async_set_updated_data(
                            LightStackState.from_dict(initial_data)
                        )
                except Exception as err:
                    _LOGGER.warning("Failed to reconnect to LightStack: %s", err)

    @callback
    def _handle_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Handle WebSocket events."""
        _LOGGER.debug(
            "Handling LightStack event: %s with data keys: %s",
            event_type,
            list(event_data.keys()) if event_data else "None",
        )

        if event_type == WS_EVENT_CURRENT_ALERT_CHANGED:
            self._handle_current_alert_changed(event_data)
        elif event_type == WS_EVENT_ALERT_TRIGGERED:
            self._handle_alert_triggered(event_data)
        elif event_type == WS_EVENT_ALERT_CLEARED:
            self._handle_alert_cleared(event_data)
        elif event_type == WS_EVENT_ALL_ALERTS_CLEARED:
            self._handle_all_alerts_cleared(event_data)
        elif event_type == "reconnected":
            # Handle reconnection with new state
            state_data = event_data.get("state", {})
            self.async_set_updated_data(LightStackState.from_dict(state_data))
        elif event_type == "disconnected":
            _LOGGER.warning("LightStack WebSocket disconnected")

    def _handle_current_alert_changed(self, event_data: dict[str, Any]) -> None:
        """Handle current_alert_changed event."""
        current_data = event_data.get("current")
        current_alert = (
            LightStackAlert.from_dict(current_data) if current_data else None
        )

        new_state = LightStackState(
            is_all_clear=event_data.get("is_all_clear", True),
            current_alert=current_alert,
            active_count=event_data.get("active_count", 0),
            active_alerts=self.data.active_alerts if self.data else [],
        )
        self.async_set_updated_data(new_state)

    def _handle_alert_triggered(self, event_data: dict[str, Any]) -> None:
        """Handle alert_triggered event."""
        _LOGGER.debug(
            "Processing alert_triggered: current_changed=%s, alert_key=%s, new_current=%s",
            event_data.get("current_changed"),
            (
                event_data.get("alert", {}).get("alert_key")
                if event_data.get("alert")
                else None
            ),
            (
                event_data.get("new_current", {}).get("alert_key")
                if event_data.get("new_current")
                else None
            ),
        )

        # Update active alerts list with the triggered alert
        alert_data = event_data.get("alert")
        triggered_alert = LightStackAlert.from_dict(alert_data) if alert_data else None

        active_alerts = list(self.data.active_alerts) if self.data else []
        if triggered_alert:
            # Add or update the alert in the list
            existing_idx = next(
                (
                    i
                    for i, a in enumerate(active_alerts)
                    if a.alert_key == triggered_alert.alert_key
                ),
                None,
            )
            if existing_idx is not None:
                active_alerts[existing_idx] = triggered_alert
            else:
                active_alerts.append(triggered_alert)

        # Update current alert only if it changed
        if event_data.get("current_changed", False):
            new_current_data = event_data.get("new_current")
            new_current = (
                LightStackAlert.from_dict(new_current_data)
                if new_current_data
                else None
            )
        else:
            # Keep existing current alert
            new_current = self.data.current_alert if self.data else None

        # Always update state to ensure sensor reflects the triggered alert
        new_state = LightStackState(
            is_all_clear=False,
            current_alert=new_current,
            active_count=len(active_alerts),
            active_alerts=active_alerts,
        )
        _LOGGER.debug(
            "Setting new state: is_all_clear=%s, current_alert=%s, active_count=%d",
            new_state.is_all_clear,
            new_state.current_alert.alert_key if new_state.current_alert else None,
            new_state.active_count,
        )
        self.async_set_updated_data(new_state)

    def _handle_alert_cleared(self, event_data: dict[str, Any]) -> None:
        """Handle alert_cleared event."""
        # Update current alert if it changed
        new_current_data = event_data.get("new_current")
        new_current = (
            LightStackAlert.from_dict(new_current_data) if new_current_data else None
        )

        # Remove the cleared alert from active list
        alert_data = event_data.get("alert")
        cleared_key = alert_data.get("alert_key") if alert_data else None

        active_alerts = list(self.data.active_alerts) if self.data else []
        if cleared_key:
            active_alerts = [a for a in active_alerts if a.alert_key != cleared_key]

        new_state = LightStackState(
            is_all_clear=new_current is None,
            current_alert=new_current,
            active_count=len(active_alerts),
            active_alerts=active_alerts,
        )
        self.async_set_updated_data(new_state)

    def _handle_all_alerts_cleared(self, event_data: dict[str, Any]) -> None:
        """Handle all_alerts_cleared event."""
        new_state = LightStackState(
            is_all_clear=True,
            current_alert=None,
            active_count=0,
            active_alerts=[],
        )
        self.async_set_updated_data(new_state)

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        # Remove listener
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

        # Cancel maintenance task
        if self._maintain_task is not None and not self._maintain_task.done():
            self._maintain_task.cancel()
            try:
                await self._maintain_task
            except asyncio.CancelledError:
                pass
            self._maintain_task = None

        # Disconnect WebSocket
        await self.websocket.disconnect()

    async def async_trigger_alert(
        self,
        alert_key: str,
        priority: int | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Trigger an alert via the WebSocket."""
        return await self.websocket.trigger_alert(alert_key, priority, note)

    async def async_clear_alert(
        self,
        alert_key: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Clear an alert via the WebSocket."""
        return await self.websocket.clear_alert(alert_key, note)

    async def async_clear_all_alerts(
        self,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Clear all alerts via the WebSocket."""
        return await self.websocket.clear_all_alerts(note)
