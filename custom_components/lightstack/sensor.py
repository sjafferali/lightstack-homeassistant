"""Sensor platform for LightStack integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_ACTIVE_COUNT
from .const import ATTR_ALERT_KEY
from .const import ATTR_DESCRIPTION
from .const import ATTR_EFFECTIVE_PRIORITY
from .const import ATTR_IS_ALL_CLEAR
from .const import ATTR_LAST_TRIGGERED
from .const import ATTR_LED_COLOR
from .const import ATTR_LED_COLOR_NAME
from .const import ATTR_LED_EFFECT
from .const import ATTR_PRIORITY_NAME
from .const import DOMAIN
from .const import ICON_ALERT
from .const import ICON_CHECK_CIRCLE
from .const import LED_COLOR_NAMES
from .const import PRIORITY_NAMES
from .const import STATE_ALL_CLEAR
from .coordinator import LightStackCoordinator
from .entity import LightStackEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LightStack sensor based on a config entry."""
    coordinator: LightStackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LightStackCurrentAlertSensor(coordinator, entry.entry_id)])


class LightStackCurrentAlertSensor(LightStackEntity, SensorEntity):
    """Sensor showing the current (highest priority) active alert."""

    _attr_translation_key = "current_alert"

    def __init__(
        self,
        coordinator: LightStackCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_current_alert"

    @property
    def native_value(self) -> str:
        """Return the current alert name or 'All Clear'."""
        if self.coordinator.data is None:
            return STATE_ALL_CLEAR

        if self.coordinator.data.is_all_clear:
            return STATE_ALL_CLEAR

        alert = self.coordinator.data.current_alert
        if alert is None:
            return STATE_ALL_CLEAR

        return alert.name or alert.alert_key

    @property
    def icon(self) -> str:
        """Return the icon based on alert status."""
        if self.coordinator.data is None or self.coordinator.data.is_all_clear:
            return ICON_CHECK_CIRCLE
        return ICON_ALERT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {
                ATTR_IS_ALL_CLEAR: True,
                ATTR_ACTIVE_COUNT: 0,
            }

        attrs = {
            ATTR_IS_ALL_CLEAR: self.coordinator.data.is_all_clear,
            ATTR_ACTIVE_COUNT: self.coordinator.data.active_count,
        }

        alert = self.coordinator.data.current_alert
        if alert is not None:
            attrs[ATTR_ALERT_KEY] = alert.alert_key
            attrs[ATTR_EFFECTIVE_PRIORITY] = alert.effective_priority
            attrs[ATTR_PRIORITY_NAME] = PRIORITY_NAMES.get(
                alert.effective_priority, "Unknown"
            )
            attrs[ATTR_LED_COLOR] = alert.led_color
            attrs[ATTR_LED_COLOR_NAME] = self._get_color_name(alert.led_color)
            attrs[ATTR_LED_EFFECT] = alert.led_effect
            attrs[ATTR_LAST_TRIGGERED] = alert.last_triggered_at
            attrs[ATTR_DESCRIPTION] = alert.description

        return attrs

    def _get_color_name(self, color_value: int | None) -> str | None:
        """Get the color name for a color value."""
        if color_value is None:
            return None

        # Find the closest color name
        if color_value in LED_COLOR_NAMES:
            return LED_COLOR_NAMES[color_value]

        # Find the closest match
        closest_color = min(LED_COLOR_NAMES.keys(), key=lambda x: abs(x - color_value))
        return LED_COLOR_NAMES[closest_color]
