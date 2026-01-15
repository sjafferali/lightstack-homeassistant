"""Base entity for LightStack integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, NAME, VERSION
from .coordinator import LightStackCoordinator


class LightStackEntity(CoordinatorEntity[LightStackCoordinator]):
    """Base class for LightStack entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LightStackCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this LightStack instance."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            model="Alert Manager",
            sw_version=VERSION,
            configuration_url=(
                f"ws://{self.coordinator.websocket._host}"
                f":{self.coordinator.websocket._port}/api/v1/ws"
            ),
        )
