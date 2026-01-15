"""Binary sensor platform for LightStack integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_ACTIVE_COUNT,
    DOMAIN,
    ICON_ALERT_CIRCLE,
    ICON_CHECK_CIRCLE,
)
from .coordinator import LightStackCoordinator
from .entity import LightStackEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LightStack binary sensor based on a config entry."""
    coordinator: LightStackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LightStackAlertActiveSensor(coordinator, entry.entry_id)])


class LightStackAlertActiveSensor(LightStackEntity, BinarySensorEntity):
    """Binary sensor indicating if any alert is active."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "alert_active"

    def __init__(
        self,
        coordinator: LightStackCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_alert_active"

    @property
    def is_on(self) -> bool:
        """Return True if any alert is active."""
        if self.coordinator.data is None:
            return False
        return not self.coordinator.data.is_all_clear

    @property
    def icon(self) -> str:
        """Return the icon based on alert status."""
        return ICON_ALERT_CIRCLE if self.is_on else ICON_CHECK_CIRCLE

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {ATTR_ACTIVE_COUNT: 0}

        return {
            ATTR_ACTIVE_COUNT: self.coordinator.data.active_count,
        }
