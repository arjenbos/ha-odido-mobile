"""Sensor platform for the Odido integration."""

from __future__ import annotations

import logging
from typing import Any, Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OdidoCoordinator
from .structs.Subscription import Subscription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Odido sensors based on a config entry."""
    _LOGGER.debug("Setting up Odido sensors")

    odido_api = hass.data[DOMAIN][entry.entry_id]["odido_api"]

    coordinator = OdidoCoordinator(hass, odido_api)
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator for possible future use by other platforms
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    sensors: list[OdidoSubscriptionSensor] = []

    for msisdn in coordinator.data:
        sensors.append(
            OdidoSubscriptionSensor(
                coordinator,
                OdidoEntityDescription(
                    key="msisdn",
                    name="Phone Number",
                    value_fn=lambda sensor: sensor.subscription.msisdn,
                ),
                msisdn,
            )
        )

        sensors.append(
            OdidoSubscriptionSensor(
                coordinator,
                OdidoEntityDescription(
                    key="agreement.start_date",
                    name="Start Date",
                    device_class=SensorDeviceClass.DATE,
                    value_fn=lambda sensor: sensor.subscription.agreement.start_date.strftime(
                        "%Y-%m-%d"
                    ),
                ),
                msisdn,
            )
        )

        sensors.append(
            OdidoSubscriptionSensor(
                coordinator,
                OdidoEntityDescription(
                    key="data_used",
                    name="Data used",
                    device_class=SensorDeviceClass.DATA_SIZE,
                    value_fn=lambda sensor: sensor.mb_used_in_bundles,
                ),
                msisdn,
            )
        )

        sensors.append(
            OdidoSubscriptionSensor(
                coordinator,
                OdidoEntityDescription(
                    key="data_left",
                    name="Data Left",
                    device_class=SensorDeviceClass.DATA_SIZE,
                    value_fn=lambda sensor: sensor.mb_left_in_bundles,
                ),
                msisdn,
            )
        )

    async_add_entities(sensors)


class OdidoSubscriptionSensor(CoordinatorEntity[OdidoCoordinator], SensorEntity):
    """Representation of an Odido subscription sensor."""

    entity_description: OdidoEntityDescription

    def __init__(
        self,
        coordinator: OdidoCoordinator,
        entity_description: OdidoEntityDescription,
        msisdn: str,
    ) -> None:
        """Initialize the Odido subscription sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._msisdn = msisdn
        self._attr_name = entity_description.name

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data[self._msisdn]

    @property
    def subscription(self) -> Subscription:
        return self._data["subscription"]

    @property
    def mb_left_in_bundles(self) -> float:
        return self._data["mb_left_in_bundles"]

    @property
    def mb_used_in_bundles(self) -> float:
        return self._data["mb_used_in_bundles"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self)

    @property
    def device_info(self) -> DeviceInfo:
        subscription = self.subscription
        return DeviceInfo(
            identifiers={(DOMAIN, subscription.msisdn)},
            name=subscription.alias or subscription.msisdn,
            manufacturer="Odido",
        )

    @property
    def unique_id(self) -> str:
        return f"{self._msisdn}_{self.entity_description.key}"

    @property
    def extra_state_attributes(self):
        subscription = self.subscription
        return {"subscription_url": subscription.subscription_url}


@dataclass(frozen=True, kw_only=True)
class OdidoEntityDescription(SensorEntityDescription):
    """Describes Odido sensor entity."""

    value_fn: Callable[["OdidoSubscriptionSensor"], float | str | None]

