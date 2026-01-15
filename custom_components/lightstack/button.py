"""Button platform for LightStack integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ICON_CLEAR_ALL
from .coordinator import LightStackCoordinator
from .entity import LightStackEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LightStack button based on a config entry."""
    coordinator: LightStackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LightStackClearAllButton(coordinator, entry.entry_id)])


class LightStackClearAllButton(LightStackEntity, ButtonEntity):
    """Button to clear all active alerts."""

    _attr_icon = ICON_CLEAR_ALL
    _attr_translation_key = "clear_all_alerts"

    def __init__(
        self,
        coordinator: LightStackCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_clear_all"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_clear_all_alerts(
            note="Cleared via Home Assistant button"
        )
